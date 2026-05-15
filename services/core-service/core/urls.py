from django.urls import path
from . import views

urlpatterns = [
    # ENO
    path('enos/', views.ENOListView.as_view(), name='eno_list'),
    path('enos/<int:pk>/', views.ENODetailView.as_view(), name='eno_detail'),

    # Spécialités
    path('specialites/', views.SpecialiteListView.as_view(), name='specialite_list'),

    # Cohortes
    path('cohortes/', views.CohorteListCreateView.as_view(), name='cohorte_list_create'),
    path('cohortes/<int:pk>/', views.CohorteDetailView.as_view(), name='cohorte_detail'),

    # Import CSV et données synthétiques
    path('import-csv/', views.import_csv_view, name='import_csv'),
    path('generer-donnees/', views.generer_donnees_view, name='generer_donnees'),

    # Apprenants
    path('apprenants/', views.ApprenantListView.as_view(), name='apprenant_list'),
    path('apprenants/<int:pk>/', views.ApprenantDetailView.as_view(), name='apprenant_detail'),
    path('mon-groupe/', views.mon_groupe_view, name='mon_groupe'),

    # Regroupements
    path('regroupements/', views.RegroupementListView.as_view(), name='regroupement_list'),
    path('regroupements/<int:pk>/', views.RegroupementDetailView.as_view(), name='regroupement_detail'),
    path('regroupements/lancer/', views.lancer_regroupement_view, name='lancer_regroupement'),
    path('regroupements/<int:pk>/progression/', views.progression_regroupement_view, name='progression_regroupement'),
    path('regroupements/<int:pk>/valider/', views.valider_regroupement_view, name='valider_regroupement'),
    path('regroupements/<int:pk>/metriques/', views.metriques_regroupement_view, name='metriques_regroupement'),
    path('regroupements/<int:pk>/export-csv/', views.export_csv_view, name='export_csv'),
    path('regroupements/<int:pk>/export-pdf/', views.export_pdf_view, name='export_pdf'),
    path('regroupements/<int:regroupement_pk>/deplacer-apprenant/', views.deplacer_apprenant_view, name='deplacer_apprenant'),

    # Groupes
    path('groupes/', views.GroupeListView.as_view(), name='groupe_list'),
    path('groupes/<int:pk>/', views.GroupeDetailView.as_view(), name='groupe_detail'),

    # Journal d'audit
    path('journal/', views.JournalAuditListView.as_view(), name='journal_list'),
]
