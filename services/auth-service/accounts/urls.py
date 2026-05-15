from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profil/', views.profil_view, name='profil'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('utilisateurs/', views.UtilisateurListView.as_view(), name='utilisateurs_list'),
    path('utilisateurs/<int:pk>/', views.UtilisateurDetailView.as_view(), name='utilisateurs_detail'),
]
