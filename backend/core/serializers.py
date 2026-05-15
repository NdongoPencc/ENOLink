from rest_framework import serializers
from .models import ENO, Specialite, Cohorte, Apprenant, Regroupement, Groupe, MembreGroupe, JournalAudit


class ENOSerializer(serializers.ModelSerializer):
    nb_apprenants = serializers.SerializerMethodField()

    class Meta:
        model = ENO
        fields = ['id', 'code', 'nom', 'region', 'ville', 'latitude', 'longitude', 'est_actif', 'nb_apprenants']

    def get_nb_apprenants(self, obj):
        cohorte_id = self.context.get('cohorte_id')
        if cohorte_id:
            return obj.apprenants.filter(cohorte_id=cohorte_id).count()
        return obj.apprenants.count()


class SpecialiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialite
        fields = ['id', 'code', 'nom', 'niveau', 'est_active']


class CohorteSerializer(serializers.ModelSerializer):
    specialite = SpecialiteSerializer(read_only=True)
    specialite_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialite.objects.all(), source='specialite', write_only=True
    )
    cree_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Cohorte
        fields = [
            'id', 'label', 'annee_academique', 'specialite', 'specialite_id',
            'statut', 'nb_apprenants', 'date_creation', 'date_modification', 'cree_par_nom'
        ]
        read_only_fields = ['id', 'statut', 'nb_apprenants', 'date_creation', 'date_modification']

    def get_cree_par_nom(self, obj):
        return obj.cree_par.nom_complet if obj.cree_par else None


class ApprenantSerializer(serializers.ModelSerializer):
    eno = ENOSerializer(read_only=True)
    eno_id = serializers.PrimaryKeyRelatedField(
        queryset=ENO.objects.all(), source='eno', write_only=True
    )
    specialite = SpecialiteSerializer(read_only=True)
    cohorte_label = serializers.SerializerMethodField()

    class Meta:
        model = Apprenant
        fields = [
            'id', 'ine', 'nom', 'prenom', 'email', 'nom_complet',
            'latitude', 'longitude', 'eno', 'eno_id', 'cohorte', 'cohorte_label',
            'specialite', 'date_import'
        ]
        read_only_fields = ['id', 'date_import', 'nom_complet']

    def get_cohorte_label(self, obj):
        return obj.cohorte.label if obj.cohorte else None


class ApprenantListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    eno_nom = serializers.CharField(source='eno.nom', read_only=True)
    eno_code = serializers.CharField(source='eno.code', read_only=True)

    class Meta:
        model = Apprenant
        fields = ['id', 'ine', 'nom', 'prenom', 'email', 'latitude', 'longitude',
                  'eno_nom', 'eno_code', 'eno_id']


class MembreGroupeSerializer(serializers.ModelSerializer):
    apprenant = ApprenantListSerializer(read_only=True)
    eno_administratif_nom = serializers.CharField(source='eno_administratif.nom', read_only=True)

    class Meta:
        model = MembreGroupe
        fields = ['id', 'apprenant', 'distance_eno_km', 'est_hors_eno', 'eno_administratif_nom']


class GroupeSerializer(serializers.ModelSerializer):
    membres = MembreGroupeSerializer(many=True, read_only=True)
    eno_rattachement = ENOSerializer(read_only=True)

    class Meta:
        model = Groupe
        fields = [
            'id', 'numero', 'eno_rattachement', 'taille',
            'dist_moy_km', 'dist_max_km', 'nb_hors_eno',
            'membres', 'date_creation'
        ]


class GroupeListSerializer(serializers.ModelSerializer):
    """Version allégée sans membres pour les listes."""
    eno_nom = serializers.CharField(source='eno_rattachement.nom', read_only=True)
    eno_region = serializers.CharField(source='eno_rattachement.region', read_only=True)
    eno_latitude = serializers.FloatField(source='eno_rattachement.latitude', read_only=True)
    eno_longitude = serializers.FloatField(source='eno_rattachement.longitude', read_only=True)

    class Meta:
        model = Groupe
        fields = [
            'id', 'numero', 'eno_nom', 'eno_region', 'eno_latitude', 'eno_longitude',
            'taille', 'dist_moy_km', 'dist_max_km', 'nb_hors_eno'
        ]


class RegroupementSerializer(serializers.ModelSerializer):
    cohorte = CohorteSerializer(read_only=True)
    cohorte_id = serializers.PrimaryKeyRelatedField(
        queryset=Cohorte.objects.all(), source='cohorte', write_only=True
    )
    lance_par_nom = serializers.SerializerMethodField()
    groupes = GroupeListSerializer(many=True, read_only=True)

    class Meta:
        model = Regroupement
        fields = [
            'id', 'cohorte', 'cohorte_id',
            'w1', 'w2', 'taille_min', 'taille_max', 'nb_generations', 'taille_population', 'seed',
            'statut', 'd_geo_final', 'p_eno_final', 'fitness_final',
            'nb_groupes', 'nb_hors_eno', 'variance_territoriale', 'temps_execution_sec',
            'message_erreur', 'progression_data',
            'date_creation', 'date_modification', 'lance_par_nom',
            'groupes'
        ]
        read_only_fields = [
            'id', 'statut', 'd_geo_final', 'p_eno_final', 'fitness_final',
            'nb_groupes', 'nb_hors_eno', 'variance_territoriale', 'temps_execution_sec',
            'message_erreur', 'progression_data', 'date_creation', 'date_modification'
        ]

    def get_lance_par_nom(self, obj):
        return obj.lance_par.nom_complet if obj.lance_par else None

    def validate(self, data):
        w1 = data.get('w1', 0.7)
        w2 = data.get('w2', 0.3)
        if abs(w1 + w2 - 1.0) > 0.001:
            raise serializers.ValidationError("w₁ + w₂ doit être égal à 1.")
        if data.get('taille_min', 3) > data.get('taille_max', 6):
            raise serializers.ValidationError("La taille minimale ne peut pas dépasser la taille maximale.")
        return data


class RegroupementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regroupement
        fields = ['cohorte', 'w1', 'w2', 'taille_min', 'taille_max', 'nb_generations', 'taille_population', 'seed']

    def validate(self, data):
        w1 = data.get('w1', 0.7)
        w2 = data.get('w2', 0.3)
        if abs(w1 + w2 - 1.0) > 0.001:
            raise serializers.ValidationError("w₁ + w₂ doit être égal à 1.")
        if data.get('taille_min', 3) > data.get('taille_max', 6):
            raise serializers.ValidationError("La taille minimale ne peut pas dépasser la taille maximale.")
        return data


class JournalAuditSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.SerializerMethodField()

    class Meta:
        model = JournalAudit
        fields = ['id', 'utilisateur_nom', 'action', 'description', 'objet_type', 'objet_id', 'date']

    def get_utilisateur_nom(self, obj):
        return obj.utilisateur.nom_complet if obj.utilisateur else 'Système'


class ImportCSVSerializer(serializers.Serializer):
    fichier = serializers.FileField()
    cohorte_label = serializers.CharField(max_length=200)
    annee_academique = serializers.CharField(max_length=9)
    specialite_id = serializers.IntegerField()

    def validate_annee_academique(self, value):
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError("Format attendu : AAAA-AAAA (ex: 2025-2026)")
        return value

    def validate_fichier(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Seuls les fichiers CSV sont acceptés.")
        if value.size > 10 * 1024 * 1024:  # 10 MB max
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 MB.")
        return value


class DeplacerApprenantSerializer(serializers.Serializer):
    apprenant_id = serializers.IntegerField()
    groupe_destination_id = serializers.IntegerField()
