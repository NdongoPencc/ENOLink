from django.db import models


class ENO(models.Model):
    """Les 18 Espaces Numériques Ouverts de l'UN-CHK."""
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=200)
    region = models.CharField(max_length=100)
    ville = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    est_actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'ENO'
        verbose_name_plural = 'ENO'
        ordering = ['region', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.region})"


class Specialite(models.Model):
    """Filière ou domaine de formation."""
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=200)
    niveau = models.CharField(
        max_length=20,
        choices=[('LICENCE', 'Licence'), ('MASTER', 'Master')],
        default='LICENCE'
    )
    est_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Spécialité'
        verbose_name_plural = 'Spécialités'
        ordering = ['niveau', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.niveau})"


class Cohorte(models.Model):
    """Ensemble d'apprenants d'une même promotion et spécialité."""
    class Statut(models.TextChoices):
        IMPORTEE = 'IMPORTEE', 'Importée'
        PRETE = 'PRETE', 'Prête'
        EN_COURS = 'EN_COURS', 'Regroupement en cours'
        REGROUPEE = 'REGROUPEE', 'Regroupée'
        VALIDEE = 'VALIDEE', 'Validée'

    label = models.CharField(max_length=200)
    annee_academique = models.CharField(max_length=9)  # ex: 2025-2026
    specialite = models.ForeignKey(Specialite, on_delete=models.PROTECT, related_name='cohortes')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.IMPORTEE)
    nb_apprenants = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par_id = models.IntegerField(null=True, blank=True, verbose_name='ID utilisateur (auth-service)')

    class Meta:
        verbose_name = 'Cohorte'
        verbose_name_plural = 'Cohortes'
        ordering = ['-annee_academique', 'label']

    def __str__(self):
        return f"{self.label} — {self.annee_academique}"

    def update_nb_apprenants(self):
        self.nb_apprenants = self.apprenants.count()
        self.save(update_fields=['nb_apprenants'])


class Apprenant(models.Model):
    """Apprenant avec ses données géographiques et administratives."""
    # Identifiants
    ine = models.CharField(max_length=50, unique=True, verbose_name='INE')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()

    # Données géographiques (seules variables utilisées par le CGA)
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Affectation administrative
    eno = models.ForeignKey(ENO, on_delete=models.PROTECT, related_name='apprenants')
    cohorte = models.ForeignKey(Cohorte, on_delete=models.CASCADE, related_name='apprenants')
    specialite = models.ForeignKey(Specialite, on_delete=models.PROTECT, related_name='apprenants')

    utilisateur_id = models.IntegerField(null=True, blank=True, verbose_name='ID utilisateur (auth-service)')

    date_import = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Apprenant'
        verbose_name_plural = 'Apprenants'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.ine})"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Regroupement(models.Model):
    """Paramètres et résultats d'une exécution du CGA."""
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        EN_COURS = 'EN_COURS', 'En cours d\'exécution'
        TERMINE = 'TERMINE', 'Terminé'
        VALIDE = 'VALIDE', 'Validé'
        ERREUR = 'ERREUR', 'Erreur'

    cohorte = models.ForeignKey(Cohorte, on_delete=models.CASCADE, related_name='regroupements')

    # Paramètres CGA
    w1 = models.FloatField(default=0.7, verbose_name='Poids géographique (w₁)')
    w2 = models.FloatField(default=0.3, verbose_name='Poids institutionnel (w₂)')
    taille_min = models.PositiveIntegerField(default=3)
    taille_max = models.PositiveIntegerField(default=6)
    nb_generations = models.PositiveIntegerField(default=200)
    taille_population = models.PositiveIntegerField(default=100)
    seed = models.PositiveIntegerField(default=42)

    # Résultats
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    d_geo_final = models.FloatField(null=True, blank=True, verbose_name='D_geo final (km)')
    p_eno_final = models.FloatField(null=True, blank=True, verbose_name='P_ENO final')
    fitness_final = models.FloatField(null=True, blank=True)
    nb_groupes = models.PositiveIntegerField(null=True, blank=True)
    nb_hors_eno = models.PositiveIntegerField(null=True, blank=True)
    variance_territoriale = models.FloatField(null=True, blank=True)
    temps_execution_sec = models.FloatField(null=True, blank=True)
    message_erreur = models.TextField(blank=True)

    # Progression (stockée en JSON pour le suivi temps réel)
    progression_data = models.JSONField(default=list, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    lance_par_id = models.IntegerField(null=True, blank=True, verbose_name='ID utilisateur (auth-service)')

    class Meta:
        verbose_name = 'Regroupement'
        verbose_name_plural = 'Regroupements'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Regroupement {self.id} — {self.cohorte} ({self.statut})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if abs(self.w1 + self.w2 - 1.0) > 0.001:
            raise ValidationError("w₁ + w₂ doit être égal à 1.")
        if self.taille_min > self.taille_max:
            raise ValidationError("La taille minimale ne peut pas dépasser la taille maximale.")


class Groupe(models.Model):
    """Groupe d'apprenants résultant d'un regroupement."""
    regroupement = models.ForeignKey(Regroupement, on_delete=models.CASCADE, related_name='groupes')
    cohorte = models.ForeignKey(Cohorte, on_delete=models.CASCADE, related_name='groupes')
    eno_rattachement = models.ForeignKey(ENO, on_delete=models.PROTECT, related_name='groupes')
    numero = models.PositiveIntegerField()

    # Métriques géographiques
    dist_moy_km = models.FloatField(default=0.0, verbose_name='Distance moyenne (km)')
    dist_max_km = models.FloatField(default=0.0, verbose_name='Distance maximale (km)')
    nb_hors_eno = models.PositiveIntegerField(default=0, verbose_name='Nb apprenants hors ENO')
    taille = models.PositiveIntegerField(default=0)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Groupe'
        verbose_name_plural = 'Groupes'
        ordering = ['regroupement', 'numero']
        unique_together = ['regroupement', 'numero']

    def __str__(self):
        return f"Groupe {self.numero} — ENO {self.eno_rattachement.nom}"


class MembreGroupe(models.Model):
    """Association apprenant ↔ groupe avec métadonnées."""
    groupe = models.ForeignKey(Groupe, on_delete=models.CASCADE, related_name='membres')
    apprenant = models.ForeignKey(Apprenant, on_delete=models.CASCADE, related_name='appartenances')
    distance_eno_km = models.FloatField(default=0.0)
    est_hors_eno = models.BooleanField(default=False)
    eno_administratif = models.ForeignKey(
        ENO,
        on_delete=models.PROTECT,
        related_name='membres_administratifs',
        null=True
    )

    class Meta:
        verbose_name = 'Membre de groupe'
        verbose_name_plural = 'Membres de groupes'
        unique_together = ['groupe', 'apprenant']

    def __str__(self):
        return f"{self.apprenant.nom_complet} → Groupe {self.groupe.numero}"


class JournalAudit(models.Model):
    """Trace toutes les actions importantes du système."""
    class Action(models.TextChoices):
        IMPORT_CSV = 'IMPORT_CSV', 'Import CSV'
        LANCEMENT_CGA = 'LANCEMENT_CGA', 'Lancement CGA'
        VALIDATION_GROUPES = 'VALIDATION_GROUPES', 'Validation des groupes'
        AJUSTEMENT_MANUEL = 'AJUSTEMENT_MANUEL', 'Ajustement manuel'
        EXPORT_CSV = 'EXPORT_CSV', 'Export CSV'
        EXPORT_PDF = 'EXPORT_PDF', 'Export PDF'
        CONNEXION = 'CONNEXION', 'Connexion'
        DECONNEXION = 'DECONNEXION', 'Déconnexion'

    utilisateur_id = models.IntegerField(null=True, blank=True, verbose_name='ID utilisateur (auth-service)')
    action = models.CharField(max_length=30, choices=Action.choices)
    description = models.TextField()
    objet_type = models.CharField(max_length=50, blank=True)
    objet_id = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Journal d\'audit'
        verbose_name_plural = 'Journal d\'audit'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} — {self.utilisateur} — {self.action}"

    @classmethod
    def log(cls, utilisateur_id, action, description, objet_type='', objet_id=None, ip=None):
        return cls.objects.create(
            utilisateur_id=utilisateur_id,
            action=action,
            description=description,
            objet_type=objet_type,
            objet_id=objet_id,
            ip_address=ip
        )
