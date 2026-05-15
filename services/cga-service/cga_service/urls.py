from django.urls import path
from algorithm.views import lancer_cga_view, statut_cga_view

urlpatterns = [
    path('api/cga/lancer/', lancer_cga_view),
    path('api/cga/<int:job_id>/statut/', statut_cga_view),
]
