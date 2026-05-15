from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Utilisateur.Role.DFIP)
        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        DFIP = 'DFIP', 'Direction de la Formation et de l\'Ingénierie Pédagogique'
        ENSEIGNANT = 'ENSEIGNANT', 'Enseignant / Pôle'
        COORDINATEUR = 'COORDINATEUR', 'Coordinateur ENO'
        APPRENANT = 'APPRENANT', 'Apprenant'

    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPRENANT)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'role']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def is_dfip(self):
        return self.role == self.Role.DFIP

    @property
    def is_enseignant(self):
        return self.role == self.Role.ENSEIGNANT

    @property
    def is_coordinateur(self):
        return self.role == self.Role.COORDINATEUR

    @property
    def is_apprenant(self):
        return self.role == self.Role.APPRENANT
