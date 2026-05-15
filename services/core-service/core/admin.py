from django.contrib import admin
from .models import ENO, Specialite, Cohorte, Apprenant, Regroupement, Groupe, MembreGroupe, JournalAudit


@admin.register(ENO)
class ENOAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'region', 'ville', 'latitude', 'longitude', 'est_actif']
    list_filter = ['region', 'est_actif']
    search_fields = ['code', 'nom', 'ville']


@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'niveau', 'est_active']
    list_filter = ['niveau', 'est_active']
    search_fields = ['code', 'nom']


@admin.register(Cohorte)
class CohorteAdmin(admin.ModelAdmin):
    list_display = ['label', 'annee_academique', 'specialite', 'statut', 'nb_apprenants', 'date_creation']
    list_filter = ['statut', 'annee_academique', 'specialite__niveau']
    search_fields = ['label']
    readonly_fields = ['nb_apprenants', 'date_creation', 'date_modification']


@admin.register(Apprenant)
class ApprenantAdmin(admin.ModelAdmin):
    list_display = ['ine', 'nom', 'prenom', 'email', 'eno', 'cohorte']
    list_filter = ['eno__region', 'cohorte']
    search_fields = ['ine', 'nom', 'prenom', 'email']
    raw_id_fields = ['eno', 'cohorte', 'specialite']


@admin.register(Regroupement)
class RegroupementAdmin(admin.ModelAdmin):
    list_display = ['id', 'cohorte', 'statut', 'w1', 'w2', 'nb_groupes', 'd_geo_final', 'p_eno_final', 'date_creation']
    list_filter = ['statut']
    readonly_fields = ['statut', 'd_geo_final', 'p_eno_final', 'fitness_final', 'nb_groupes',
                       'nb_hors_eno', 'variance_territoriale', 'temps_execution_sec', 'date_creation']


@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero', 'regroupement', 'eno_rattachement', 'taille', 'dist_moy_km', 'nb_hors_eno']
    list_filter = ['eno_rattachement__region']
    raw_id_fields = ['regroupement', 'cohorte', 'eno_rattachement']


@admin.register(MembreGroupe)
class MembreGroupeAdmin(admin.ModelAdmin):
    list_display = ['apprenant', 'groupe', 'distance_eno_km', 'est_hors_eno']
    list_filter = ['est_hors_eno']
    raw_id_fields = ['groupe', 'apprenant', 'eno_administratif']


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ['date', 'utilisateur_id', 'action', 'description', 'objet_type', 'objet_id']
    list_filter = ['action']
    readonly_fields = ['date']
    search_fields = ['description']
