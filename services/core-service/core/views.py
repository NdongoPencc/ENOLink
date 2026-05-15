import csv
import io
import threading

from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_service.permissions import IsDFIP, IsEnseignantOrCoordinateur
from .models import (
    ENO, Specialite, Cohorte, Apprenant,
    Regroupement, Groupe, MembreGroupe, JournalAudit
)
from .serializers import (
    ENOSerializer, SpecialiteSerializer, CohorteSerializer,
    ApprenantSerializer, ApprenantListSerializer,
    RegroupementSerializer, RegroupementCreateSerializer,
    GroupeSerializer, GroupeListSerializer,
    JournalAuditSerializer,
    ImportCSVSerializer, DeplacerApprenantSerializer,
)


# ─── ENO ────────────────────────────────────────────────────────────────────

class ENOListView(generics.ListAPIView):
    queryset = ENO.objects.filter(est_actif=True)
    serializer_class = ENOSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        cohorte_id = self.request.query_params.get('cohorte_id')
        if cohorte_id:
            ctx['cohorte_id'] = cohorte_id
        return ctx


class ENODetailView(generics.RetrieveAPIView):
    queryset = ENO.objects.all()
    serializer_class = ENOSerializer
    permission_classes = [IsAuthenticated]


# ─── SPÉCIALITÉ ─────────────────────────────────────────────────────────────

class SpecialiteListView(generics.ListAPIView):
    queryset = Specialite.objects.filter(est_active=True)
    serializer_class = SpecialiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        niveau = self.request.query_params.get('niveau')
        if niveau:
            qs = qs.filter(niveau=niveau)
        return qs


# ─── COHORTE ─────────────────────────────────────────────────────────────────

class CohorteListCreateView(generics.ListCreateAPIView):
    serializer_class = CohorteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Cohorte.objects.select_related('specialite').all()
        statut = self.request.query_params.get('statut')
        annee = self.request.query_params.get('annee')
        if statut:
            qs = qs.filter(statut=statut)
        if annee:
            qs = qs.filter(annee_academique=annee)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsDFIP()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        cohorte = serializer.save(cree_par_id=self.request.user.id)
        JournalAudit.log(
            self.request.user.id,
            JournalAudit.Action.IMPORT_CSV,
            f"Cohorte créée : {cohorte.label}",
            objet_type='Cohorte',
            objet_id=cohorte.id,
        )


class CohorteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cohorte.objects.select_related('specialite').all()
    serializer_class = CohorteSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsDFIP()]


# ─── IMPORT CSV ──────────────────────────────────────────────────────────────

COLONNES_REQUISES = {'ine', 'nom', 'prenom', 'email', 'latitude', 'longitude', 'eno_code'}

LAT_MIN, LAT_MAX = 12.3, 16.7
LON_MIN, LON_MAX = -17.5, -11.3


@api_view(['POST'])
@permission_classes([IsDFIP])
def import_csv_view(request):
    serializer = ImportCSVSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    fichier = serializer.validated_data['fichier']
    label = serializer.validated_data['cohorte_label']
    annee = serializer.validated_data['annee_academique']
    specialite_id = serializer.validated_data['specialite_id']

    try:
        specialite = Specialite.objects.get(id=specialite_id)
    except Specialite.DoesNotExist:
        return Response({'error': 'Spécialité introuvable.'}, status=status.HTTP_400_BAD_REQUEST)

    # Lire le CSV
    try:
        contenu = fichier.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(contenu))
        lignes = list(reader)
    except Exception as e:
        return Response({'error': f'Erreur de lecture du fichier : {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    if not lignes:
        return Response({'error': 'Le fichier CSV est vide.'}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier les colonnes
    colonnes_presentes = set(lignes[0].keys())
    colonnes_manquantes = COLONNES_REQUISES - colonnes_presentes
    if colonnes_manquantes:
        return Response(
            {'error': f'Colonnes manquantes : {", ".join(colonnes_manquantes)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Charger les ENO
    enos_map = {eno.code: eno for eno in ENO.objects.all()}

    erreurs = []
    apprenants_valides = []
    ines_vus = set()
    enos_peu_peuples = {}

    for i, ligne in enumerate(lignes, start=2):
        ligne_erreurs = []

        ine = ligne.get('ine', '').strip()
        nom = ligne.get('nom', '').strip()
        prenom = ligne.get('prenom', '').strip()
        email = ligne.get('email', '').strip()
        eno_code = ligne.get('eno_code', '').strip()

        try:
            lat = float(ligne.get('latitude', ''))
            lon = float(ligne.get('longitude', ''))
        except ValueError:
            ligne_erreurs.append('Coordonnées GPS invalides')
            lat, lon = 0, 0

        if not ine:
            ligne_erreurs.append('INE manquant')
        elif ine in ines_vus:
            ligne_erreurs.append(f'INE dupliqué : {ine}')
        else:
            ines_vus.add(ine)

        if not nom:
            ligne_erreurs.append('Nom manquant')
        if not prenom:
            ligne_erreurs.append('Prénom manquant')
        if not email or '@' not in email:
            ligne_erreurs.append('Email invalide')

        if lat and lon:
            if not (LAT_MIN <= lat <= LAT_MAX):
                ligne_erreurs.append(f'Latitude hors limites Sénégal : {lat}')
            if not (LON_MIN <= lon <= LON_MAX):
                ligne_erreurs.append(f'Longitude hors limites Sénégal : {lon}')

        if eno_code not in enos_map:
            ligne_erreurs.append(f'Code ENO inconnu : {eno_code}')
        else:
            eno = enos_map[eno_code]
            if eno.code not in enos_peu_peuples:
                enos_peu_peuples[eno.code] = 0
            enos_peu_peuples[eno.code] += 1

        if ligne_erreurs:
            erreurs.append({'ligne': i, 'ine': ine, 'erreurs': ligne_erreurs})
        else:
            apprenants_valides.append({
                'ine': ine, 'nom': nom, 'prenom': prenom, 'email': email,
                'latitude': lat, 'longitude': lon,
                'eno': enos_map[eno_code],
            })

    if erreurs:
        return Response({
            'succes': False,
            'nb_lignes': len(lignes),
            'nb_erreurs': len(erreurs),
            'erreurs': erreurs,
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # Détecter les ENO peu peuplés (informatif, non bloquant)
    alertes_eno = []

    # Créer la cohorte et les apprenants
    with transaction.atomic():
        # Vérifier les INE existants
        ines_existants = set(
            Apprenant.objects.filter(ine__in=ines_vus).values_list('ine', flat=True)
        )

        cohorte = Cohorte.objects.create(
            label=label,
            annee_academique=annee,
            specialite=specialite,
            statut=Cohorte.Statut.PRETE,
            cree_par_id=request.user.id,
        )

        apprenants_crees = []
        for data in apprenants_valides:
            if data['ine'] in ines_existants:
                alertes_eno.append(f"INE {data['ine']} déjà existant — mis à jour")
            apprenants_crees.append(Apprenant(
                ine=data['ine'],
                nom=data['nom'],
                prenom=data['prenom'],
                email=data['email'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                eno=data['eno'],
                cohorte=cohorte,
                specialite=specialite,
            ))

        Apprenant.objects.bulk_create(apprenants_crees, ignore_conflicts=True)
        cohorte.update_nb_apprenants()

        JournalAudit.log(
            request.user.id,
            JournalAudit.Action.IMPORT_CSV,
            f"Import CSV : {len(apprenants_crees)} apprenants importés dans la cohorte '{label}'",
            objet_type='Cohorte',
            objet_id=cohorte.id,
        )

    # Calculer les ENO peu peuplés
    from algorithm.cga import CGA
    taille_min_defaut = 3
    enos_peu_peuples_liste = [
        code for code, nb in enos_peu_peuples.items() if nb < taille_min_defaut
    ]

    return Response({
        'succes': True,
        'cohorte_id': cohorte.id,
        'cohorte_label': cohorte.label,
        'nb_apprenants': cohorte.nb_apprenants,
        'repartition_eno': enos_peu_peuples,
        'enos_peu_peuples': enos_peu_peuples_liste,
        'alertes': alertes_eno,
    }, status=status.HTTP_201_CREATED)


# ─── APPRENANTS ──────────────────────────────────────────────────────────────

class ApprenantListView(generics.ListAPIView):
    serializer_class = ApprenantListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Apprenant.objects.select_related('eno', 'cohorte', 'specialite').all()
        cohorte_id = self.request.query_params.get('cohorte_id')
        eno_id = self.request.query_params.get('eno_id')
        if cohorte_id:
            qs = qs.filter(cohorte_id=cohorte_id)
        if eno_id:
            qs = qs.filter(eno_id=eno_id)
        return qs


class ApprenantDetailView(generics.RetrieveAPIView):
    queryset = Apprenant.objects.select_related('eno', 'cohorte', 'specialite').all()
    serializer_class = ApprenantSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mon_groupe_view(request):
    """Vue apprenant : consulter son groupe."""
    try:
        apprenant = request.user.apprenant_profil
    except Exception:
        return Response({'error': 'Aucun profil apprenant associé à ce compte.'}, status=404)

    membre = MembreGroupe.objects.select_related(
        'groupe', 'groupe__eno_rattachement', 'groupe__regroupement__cohorte'
    ).filter(apprenant=apprenant).order_by('-groupe__date_creation').first()

    if not membre:
        return Response({'error': 'Aucun groupe assigné pour le moment.'}, status=404)

    groupe = membre.groupe
    membres = MembreGroupe.objects.select_related('apprenant', 'eno_administratif').filter(groupe=groupe)

    return Response({
        'groupe_id': groupe.id,
        'groupe_numero': groupe.numero,
        'eno_rattachement': {
            'id': groupe.eno_rattachement.id,
            'nom': groupe.eno_rattachement.nom,
            'region': groupe.eno_rattachement.region,
            'ville': groupe.eno_rattachement.ville,
            'latitude': groupe.eno_rattachement.latitude,
            'longitude': groupe.eno_rattachement.longitude,
        },
        'est_hors_eno': membre.est_hors_eno,
        'distance_eno_km': round(membre.distance_eno_km, 2),
        'cohorte': groupe.cohorte.label,
        'membres': [
            {
                'nom': m.apprenant.nom,
                'prenom': m.apprenant.prenom,
                'email': m.apprenant.email,
                'est_hors_eno': m.est_hors_eno,
            }
            for m in membres
        ],
    })


# ─── REGROUPEMENT ────────────────────────────────────────────────────────────

class RegroupementListView(generics.ListAPIView):
    serializer_class = RegroupementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Regroupement.objects.select_related('cohorte').prefetch_related('groupes').all()
        cohorte_id = self.request.query_params.get('cohorte_id')
        if cohorte_id:
            qs = qs.filter(cohorte_id=cohorte_id)
        return qs


class RegroupementDetailView(generics.RetrieveAPIView):
    queryset = Regroupement.objects.select_related('cohorte').prefetch_related(
        'groupes__eno_rattachement', 'groupes__membres__apprenant__eno'
    ).all()
    serializer_class = RegroupementSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsDFIP])
def lancer_regroupement_view(request):
    """Lance le CGA en arrière-plan et retourne l'ID du regroupement."""
    serializer = RegroupementCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cohorte = serializer.validated_data['cohorte']

    if cohorte.statut not in [Cohorte.Statut.PRETE, Cohorte.Statut.REGROUPEE]:
        return Response(
            {'error': f"La cohorte doit être en statut 'Prête' ou 'Regroupée'. Statut actuel : {cohorte.statut}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    nb_apprenants = cohorte.apprenants.count()
    if nb_apprenants == 0:
        return Response({'error': 'La cohorte ne contient aucun apprenant.'}, status=status.HTTP_400_BAD_REQUEST)

    regroupement = serializer.save(lance_par_id=request.user.id, statut=Regroupement.Statut.EN_ATTENTE)
    cohorte.statut = Cohorte.Statut.EN_COURS
    cohorte.save(update_fields=['statut'])

    JournalAudit.log(
        request.user.id,
        JournalAudit.Action.LANCEMENT_CGA,
        f"Lancement CGA sur cohorte '{cohorte.label}' — w1={regroupement.w1}, w2={regroupement.w2}",
        objet_type='Regroupement',
        objet_id=regroupement.id,
    )

    # Lancer le CGA en arrière-plan
    thread = threading.Thread(target=_executer_cga, args=(regroupement.id,), daemon=True)
    thread.start()

    return Response({
        'regroupement_id': regroupement.id,
        'statut': regroupement.statut,
        'message': 'Regroupement lancé. Suivez la progression via /api/regroupements/{id}/progression/',
    }, status=status.HTTP_202_ACCEPTED)


def _executer_cga(regroupement_id: int):
    """Exécute le CGA en arrière-plan."""
    import django
    from algorithm.cga import CGA
    from algorithm.geo import haversine

    try:
        regroupement = Regroupement.objects.select_related('cohorte').get(id=regroupement_id)
        regroupement.statut = Regroupement.Statut.EN_COURS
        regroupement.save(update_fields=['statut'])

        cohorte = regroupement.cohorte
        apprenants_qs = Apprenant.objects.select_related('eno').filter(cohorte=cohorte)
        enos_qs = ENO.objects.all()

        # Construire les structures de données pour le CGA
        enos_dict = {
            eno.id: {
                'id': eno.id,
                'nom': eno.nom,
                'region': eno.region,
                'latitude': eno.latitude,
                'longitude': eno.longitude,
            }
            for eno in enos_qs
        }

        apprenants_list = [
            {
                'id': app.id,
                'ine': app.ine,
                'nom': app.nom,
                'prenom': app.prenom,
                'email': app.email,
                'latitude': app.latitude,
                'longitude': app.longitude,
                'eno_id': app.eno.id,
            }
            for app in apprenants_qs
        ]

        progression_data = []

        def callback(point):
            progression_data.append(point)
            # Sauvegarder la progression toutes les 10 générations
            if point['generation'] % 10 == 0:
                Regroupement.objects.filter(id=regroupement_id).update(
                    progression_data=progression_data
                )

        cga = CGA(
            apprenants=apprenants_list,
            enos=enos_dict,
            w1=regroupement.w1,
            w2=regroupement.w2,
            taille_min=regroupement.taille_min,
            taille_max=regroupement.taille_max,
            nb_generations=regroupement.nb_generations,
            taille_population=regroupement.taille_population,
            seed=regroupement.seed,
            callback_progression=callback,
        )

        resultats = cga.executer()

        if not resultats.get('succes'):
            regroupement.statut = Regroupement.Statut.ERREUR
            regroupement.message_erreur = resultats.get('erreur', 'Erreur inconnue')
            regroupement.save()
            return

        # Sauvegarder les groupes en base
        with transaction.atomic():
            # Supprimer les anciens groupes de ce regroupement
            Groupe.objects.filter(regroupement=regroupement).delete()

            for groupe_data in resultats['groupes']:
                if groupe_data['taille'] == 0:
                    continue

                eno = ENO.objects.get(id=groupe_data['eno_id'])
                groupe = Groupe.objects.create(
                    regroupement=regroupement,
                    cohorte=cohorte,
                    eno_rattachement=eno,
                    numero=groupe_data['numero'],
                    dist_moy_km=groupe_data['dist_moy_km'],
                    dist_max_km=groupe_data['dist_max_km'],
                    nb_hors_eno=groupe_data['nb_hors_eno'],
                    taille=groupe_data['taille'],
                )

                membres_a_creer = []
                for membre_data in groupe_data['membres']:
                    apprenant = Apprenant.objects.get(id=membre_data['id'])
                    dist = haversine(
                        membre_data['latitude'], membre_data['longitude'],
                        eno.latitude, eno.longitude
                    )
                    est_hors_eno = membre_data['eno_id'] != eno.id
                    membres_a_creer.append(MembreGroupe(
                        groupe=groupe,
                        apprenant=apprenant,
                        distance_eno_km=dist,
                        est_hors_eno=est_hors_eno,
                        eno_administratif=apprenant.eno,
                    ))
                MembreGroupe.objects.bulk_create(membres_a_creer)

            # Mettre à jour le regroupement
            regroupement.statut = Regroupement.Statut.TERMINE
            regroupement.d_geo_final = resultats['d_geo_final']
            regroupement.p_eno_final = resultats['p_eno_final']
            regroupement.fitness_final = resultats['fitness_final']
            regroupement.nb_groupes = resultats['nb_groupes']
            regroupement.nb_hors_eno = resultats['nb_hors_eno']
            regroupement.variance_territoriale = resultats['variance_territoriale']
            regroupement.temps_execution_sec = resultats['temps_execution_sec']
            regroupement.progression_data = resultats['historique_fitness']
            regroupement.save()

            cohorte.statut = Cohorte.Statut.REGROUPEE
            cohorte.save(update_fields=['statut'])

    except Exception as e:
        Regroupement.objects.filter(id=regroupement_id).update(
            statut=Regroupement.Statut.ERREUR,
            message_erreur=str(e),
        )
        Cohorte.objects.filter(regroupements__id=regroupement_id).update(
            statut=Cohorte.Statut.PRETE
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progression_regroupement_view(request, pk):
    """Retourne la progression courante du CGA (polling)."""
    try:
        regroupement = Regroupement.objects.get(pk=pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    return Response({
        'regroupement_id': regroupement.id,
        'statut': regroupement.statut,
        'progression': regroupement.progression_data,
        'derniere_generation': regroupement.progression_data[-1] if regroupement.progression_data else None,
        'd_geo_final': regroupement.d_geo_final,
        'p_eno_final': regroupement.p_eno_final,
        'fitness_final': regroupement.fitness_final,
        'temps_execution_sec': regroupement.temps_execution_sec,
        'message_erreur': regroupement.message_erreur,
    })


@api_view(['POST'])
@permission_classes([IsDFIP])
def valider_regroupement_view(request, pk):
    """Valide un regroupement terminé."""
    try:
        regroupement = Regroupement.objects.select_related('cohorte').get(pk=pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    if regroupement.statut != Regroupement.Statut.TERMINE:
        return Response(
            {'error': f"Le regroupement doit être terminé pour être validé. Statut : {regroupement.statut}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    regroupement.statut = Regroupement.Statut.VALIDE
    regroupement.save(update_fields=['statut'])

    regroupement.cohorte.statut = Cohorte.Statut.VALIDEE
    regroupement.cohorte.save(update_fields=['statut'])

    JournalAudit.log(
        request.user.id,
        JournalAudit.Action.VALIDATION_GROUPES,
        f"Regroupement #{pk} validé pour la cohorte '{regroupement.cohorte.label}'",
        objet_type='Regroupement',
        objet_id=pk,
    )

    return Response({'message': 'Regroupement validé avec succès.', 'statut': regroupement.statut})


# ─── GROUPES ─────────────────────────────────────────────────────────────────

class GroupeListView(generics.ListAPIView):
    serializer_class = GroupeListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Groupe.objects.select_related('eno_rattachement', 'cohorte').all()
        regroupement_id = self.request.query_params.get('regroupement_id')
        eno_id = self.request.query_params.get('eno_id')
        if regroupement_id:
            qs = qs.filter(regroupement_id=regroupement_id)
        if eno_id:
            qs = qs.filter(eno_rattachement_id=eno_id)
        return qs


class GroupeDetailView(generics.RetrieveAPIView):
    queryset = Groupe.objects.select_related('eno_rattachement').prefetch_related(
        'membres__apprenant__eno', 'membres__eno_administratif'
    ).all()
    serializer_class = GroupeSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsDFIP])
def deplacer_apprenant_view(request, regroupement_pk):
    """Déplace manuellement un apprenant d'un groupe à un autre et recalcule les métriques."""
    serializer = DeplacerApprenantSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    apprenant_id = serializer.validated_data['apprenant_id']
    groupe_dest_id = serializer.validated_data['groupe_destination_id']

    try:
        regroupement = Regroupement.objects.get(pk=regroupement_pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    if regroupement.statut not in [Regroupement.Statut.TERMINE, Regroupement.Statut.VALIDE]:
        return Response({'error': 'Le regroupement doit être terminé ou validé.'}, status=400)

    try:
        membre = MembreGroupe.objects.select_related(
            'groupe', 'apprenant', 'apprenant__eno'
        ).get(apprenant_id=apprenant_id, groupe__regroupement=regroupement)
    except MembreGroupe.DoesNotExist:
        return Response({'error': 'Apprenant introuvable dans ce regroupement.'}, status=404)

    try:
        groupe_dest = Groupe.objects.select_related('eno_rattachement').get(
            pk=groupe_dest_id, regroupement=regroupement
        )
    except Groupe.DoesNotExist:
        return Response({'error': 'Groupe de destination introuvable.'}, status=404)

    groupe_source = membre.groupe

    with transaction.atomic():
        from algorithm.geo import haversine

        # Mettre à jour le membre
        eno_dest = groupe_dest.eno_rattachement
        nouvelle_distance = haversine(
            membre.apprenant.latitude, membre.apprenant.longitude,
            eno_dest.latitude, eno_dest.longitude
        )
        est_hors_eno = membre.apprenant.eno.id != eno_dest.id

        membre.groupe = groupe_dest
        membre.distance_eno_km = nouvelle_distance
        membre.est_hors_eno = est_hors_eno
        membre.save()

        # Recalculer les métriques des deux groupes
        for groupe in [groupe_source, groupe_dest]:
            _recalculer_metriques_groupe(groupe)

        JournalAudit.log(
            request.user.id,
            JournalAudit.Action.AJUSTEMENT_MANUEL,
            f"Apprenant {membre.apprenant.nom_complet} déplacé du groupe {groupe_source.numero} vers le groupe {groupe_dest.numero}",
            objet_type='Regroupement',
            objet_id=regroupement_pk,
        )

    return Response({
        'message': 'Déplacement effectué.',
        'groupe_source': GroupeListSerializer(groupe_source).data,
        'groupe_destination': GroupeListSerializer(groupe_dest).data,
    })


def _recalculer_metriques_groupe(groupe: Groupe):
    """Recalcule et sauvegarde les métriques d'un groupe."""
    from algorithm.geo import haversine
    membres = MembreGroupe.objects.select_related('apprenant').filter(groupe=groupe)
    eno = groupe.eno_rattachement

    distances = []
    nb_hors_eno = 0
    for m in membres:
        dist = haversine(m.apprenant.latitude, m.apprenant.longitude, eno.latitude, eno.longitude)
        distances.append(dist)
        if m.est_hors_eno:
            nb_hors_eno += 1

    import numpy as np
    groupe.taille = len(distances)
    groupe.dist_moy_km = float(np.mean(distances)) if distances else 0.0
    groupe.dist_max_km = float(np.max(distances)) if distances else 0.0
    groupe.nb_hors_eno = nb_hors_eno
    groupe.save(update_fields=['taille', 'dist_moy_km', 'dist_max_km', 'nb_hors_eno'])


# ─── MÉTRIQUES ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metriques_regroupement_view(request, pk):
    """Retourne les métriques détaillées d'un regroupement."""
    try:
        regroupement = Regroupement.objects.select_related('cohorte').get(pk=pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    groupes = Groupe.objects.select_related('eno_rattachement').filter(regroupement=regroupement)

    metriques_par_eno = {}
    for groupe in groupes:
        eno_nom = groupe.eno_rattachement.nom
        if eno_nom not in metriques_par_eno:
            metriques_par_eno[eno_nom] = {
                'eno_id': groupe.eno_rattachement.id,
                'eno_nom': eno_nom,
                'eno_region': groupe.eno_rattachement.region,
                'nb_groupes': 0,
                'nb_apprenants': 0,
                'dist_moy_km': 0.0,
                'nb_hors_eno': 0,
            }
        m = metriques_par_eno[eno_nom]
        m['nb_groupes'] += 1
        m['nb_apprenants'] += groupe.taille
        m['dist_moy_km'] = (m['dist_moy_km'] * (m['nb_groupes'] - 1) + groupe.dist_moy_km) / m['nb_groupes']
        m['nb_hors_eno'] += groupe.nb_hors_eno

    return Response({
        'regroupement_id': regroupement.id,
        'cohorte': regroupement.cohorte.label,
        'statut': regroupement.statut,
        'd_geo_final': regroupement.d_geo_final,
        'p_eno_final': regroupement.p_eno_final,
        'fitness_final': regroupement.fitness_final,
        'variance_territoriale': regroupement.variance_territoriale,
        'nb_groupes': regroupement.nb_groupes,
        'nb_hors_eno': regroupement.nb_hors_eno,
        'temps_execution_sec': regroupement.temps_execution_sec,
        'metriques_par_eno': list(metriques_par_eno.values()),
        'historique_fitness': regroupement.progression_data,
    })


# ─── EXPORT CSV ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv_view(request, pk):
    """Exporte les groupes d'un regroupement en CSV."""
    try:
        regroupement = Regroupement.objects.select_related('cohorte').get(pk=pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    if regroupement.statut not in [Regroupement.Statut.TERMINE, Regroupement.Statut.VALIDE]:
        return Response({'error': 'Le regroupement doit être terminé ou validé.'}, status=400)

    membres = MembreGroupe.objects.select_related(
        'apprenant', 'apprenant__eno', 'groupe', 'groupe__eno_rattachement',
        'groupe__cohorte', 'groupe__cohorte__specialite', 'eno_administratif'
    ).filter(groupe__regroupement=regroupement).order_by('groupe__numero', 'apprenant__nom')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    nom_fichier = f"groupes_{regroupement.cohorte.label.replace(' ', '_')}_{regroupement.id}.csv"
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    response.write('\ufeff')  # BOM UTF-8 pour Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'id_apprenant', 'ine', 'nom', 'prenom', 'email',
        'id_groupe', 'numero_groupe', 'id_eno_rattachement', 'nom_eno_rattachement',
        'region_eno', 'distance_eno_km', 'hors_eno',
        'id_eno_administratif', 'nom_eno_administratif',
        'id_cohorte', 'label_cohorte', 'id_specialite', 'nom_specialite',
    ])

    for m in membres:
        writer.writerow([
            m.apprenant.id,
            m.apprenant.ine,
            m.apprenant.nom,
            m.apprenant.prenom,
            m.apprenant.email,
            m.groupe.id,
            m.groupe.numero,
            m.groupe.eno_rattachement.id,
            m.groupe.eno_rattachement.nom,
            m.groupe.eno_rattachement.region,
            round(m.distance_eno_km, 2),
            'Oui' if m.est_hors_eno else 'Non',
            m.eno_administratif.id if m.eno_administratif else '',
            m.eno_administratif.nom if m.eno_administratif else '',
            m.groupe.cohorte.id,
            m.groupe.cohorte.label,
            m.groupe.cohorte.specialite.id,
            m.groupe.cohorte.specialite.nom,
        ])

    JournalAudit.log(
        request.user.id, JournalAudit.Action.EXPORT_CSV,
        f"Export CSV du regroupement #{pk}",
        objet_type='Regroupement', objet_id=pk,
    )
    return response


# ─── EXPORT PDF ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_pdf_view(request, pk):
    """Génère un rapport PDF complet du regroupement."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io as _io

    try:
        regroupement = Regroupement.objects.select_related('cohorte', 'cohorte__specialite').get(pk=pk)
    except Regroupement.DoesNotExist:
        return Response({'error': 'Regroupement introuvable.'}, status=404)

    groupes = Groupe.objects.select_related('eno_rattachement').prefetch_related(
        'membres__apprenant', 'membres__eno_administratif'
    ).filter(regroupement=regroupement).order_by('numero')

    buffer = _io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('titre', parent=styles['Title'], fontSize=16,
                                  textColor=colors.HexColor('#1a237e'), spaceAfter=6)
    style_sous_titre = ParagraphStyle('sous_titre', parent=styles['Heading2'], fontSize=12,
                                       textColor=colors.HexColor('#283593'), spaceAfter=4)
    style_groupe = ParagraphStyle('groupe', parent=styles['Heading3'], fontSize=10,
                                   textColor=colors.HexColor('#1565c0'), spaceAfter=3)
    style_normal = styles['Normal']
    style_normal.fontSize = 9

    elements = []

    # En-tête
    elements.append(Paragraph("UNIVERSITÉ NUMÉRIQUE CHEIKH HAMIDOU KANE", style_titre))
    elements.append(Paragraph("ENOLink — Rapport de Regroupement", style_sous_titre))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a237e')))
    elements.append(Spacer(1, 0.3*cm))

    # Informations générales
    info_data = [
        ['Cohorte', regroupement.cohorte.label],
        ['Spécialité', regroupement.cohorte.specialite.nom],
        ['Année académique', regroupement.cohorte.annee_academique],
        ['Statut', regroupement.get_statut_display()],
        ['w₁ (géographique)', str(regroupement.w1)],
        ['w₂ (institutionnel)', str(regroupement.w2)],
        ['Taille des groupes', f"{regroupement.taille_min} – {regroupement.taille_max}"],
        ['Générations CGA', str(regroupement.nb_generations)],
    ]
    if regroupement.d_geo_final is not None:
        info_data += [
            ['D_geo final (km)', f"{regroupement.d_geo_final:.4f}"],
            ['P_ENO final', str(regroupement.p_eno_final)],
            ['Fitness final', f"{regroupement.fitness_final:.6f}"],
            ['Nb groupes', str(regroupement.nb_groupes)],
            ['Apprenants hors ENO', str(regroupement.nb_hors_eno)],
            ['Temps d\'exécution', f"{regroupement.temps_execution_sec:.2f} s"],
        ]

    table_info = Table(info_data, colWidths=[6*cm, 10*cm])
    table_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 0.5*cm))

    # Groupes détaillés
    elements.append(Paragraph("Détail des groupes", style_sous_titre))

    for groupe in groupes:
        elements.append(Paragraph(
            f"Groupe {groupe.numero} — ENO {groupe.eno_rattachement.nom} ({groupe.eno_rattachement.region})",
            style_groupe
        ))

        membres_data = [['INE', 'Nom', 'Prénom', 'Email', 'Dist. ENO (km)', 'Hors ENO']]
        for m in groupe.membres.all():
            membres_data.append([
                m.apprenant.ine,
                m.apprenant.nom,
                m.apprenant.prenom,
                m.apprenant.email,
                f"{m.distance_eno_km:.1f}",
                '⚠ Oui' if m.est_hors_eno else 'Non',
            ])

        table_membres = Table(membres_data, colWidths=[2.5*cm, 3*cm, 3*cm, 4.5*cm, 2*cm, 1.5*cm])
        table_membres.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(table_membres)

        metriques_txt = (
            f"Taille : {groupe.taille} | "
            f"Distance moy. : {groupe.dist_moy_km:.2f} km | "
            f"Distance max. : {groupe.dist_max_km:.2f} km | "
            f"Hors ENO : {groupe.nb_hors_eno}"
        )
        elements.append(Paragraph(metriques_txt, style_normal))
        elements.append(Spacer(1, 0.3*cm))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    nom_fichier = f"rapport_groupes_{regroupement.cohorte.label.replace(' ', '_')}_{pk}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'

    JournalAudit.log(
        request.user.id, JournalAudit.Action.EXPORT_PDF,
        f"Export PDF du regroupement #{pk}",
        objet_type='Regroupement', objet_id=pk,
    )
    return response


# ─── JOURNAL D'AUDIT ─────────────────────────────────────────────────────────

class JournalAuditListView(generics.ListAPIView):
    serializer_class = JournalAuditSerializer
    permission_classes = [IsDFIP]

    def get_queryset(self):
        qs = JournalAudit.objects.select_related('utilisateur').all()
        action = self.request.query_params.get('action')
        objet_id = self.request.query_params.get('objet_id')
        if action:
            qs = qs.filter(action=action)
        if objet_id:
            qs = qs.filter(objet_id=objet_id)
        return qs[:200]


# ─── DONNÉES SYNTHÉTIQUES ────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsDFIP])
def generer_donnees_view(request):
    """Génère des données synthétiques pour une cohorte (développement/démo)."""
    from algorithm.data_generator import generer_donnees_synthetiques, ENO_DATA
    from algorithm.geo import haversine

    nb_apprenants = int(request.data.get('nb_apprenants', 100))
    specialite_id = request.data.get('specialite_id')
    label = request.data.get('label', f'Cohorte synthétique ({nb_apprenants} apprenants)')
    annee = request.data.get('annee_academique', '2025-2026')
    seed = int(request.data.get('seed', 42))

    if nb_apprenants < 10 or nb_apprenants > 500:
        return Response({'error': 'nb_apprenants doit être entre 10 et 500.'}, status=400)

    try:
        specialite = Specialite.objects.get(id=specialite_id)
    except (Specialite.DoesNotExist, TypeError):
        return Response({'error': 'Spécialité introuvable.'}, status=400)

    donnees = generer_donnees_synthetiques(nb_apprenants=nb_apprenants, seed=seed)

    with transaction.atomic():
        cohorte = Cohorte.objects.create(
            label=label,
            annee_academique=annee,
            specialite=specialite,
            statut=Cohorte.Statut.PRETE,
            cree_par_id=request.user.id,
        )

        enos_db = {eno.code: eno for eno in ENO.objects.all()}
        apprenants_a_creer = []

        for data in donnees:
            eno_code = data['eno_code']
            if eno_code not in enos_db:
                continue
            apprenants_a_creer.append(Apprenant(
                ine=data['ine'],
                nom=data['nom'],
                prenom=data['prenom'],
                email=data['email'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                eno=enos_db[eno_code],
                cohorte=cohorte,
                specialite=specialite,
            ))

        Apprenant.objects.bulk_create(apprenants_a_creer, ignore_conflicts=True)
        cohorte.update_nb_apprenants()

        JournalAudit.log(
            request.user.id,
            JournalAudit.Action.IMPORT_CSV,
            f"Données synthétiques générées : {cohorte.nb_apprenants} apprenants (SEED={seed})",
            objet_type='Cohorte',
            objet_id=cohorte.id,
        )

    return Response({
        'cohorte_id': cohorte.id,
        'label': cohorte.label,
        'nb_apprenants': cohorte.nb_apprenants,
        'seed': seed,
    }, status=status.HTTP_201_CREATED)
