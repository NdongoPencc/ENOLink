from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Utilisateur
from .serializers import (
    UtilisateurSerializer,
    UtilisateurCreateSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsStaffOrDFIP


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurCreateSerializer
    permission_classes = [IsStaffOrDFIP]


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profil_view(request):
    if request.method == 'GET':
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)

    serializer = UtilisateurSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        request.user.set_password(serializer.validated_data['nouveau_password'])
        request.user.save()
        return Response({'message': 'Mot de passe modifié avec succès.'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Déconnexion réussie.'})
    except Exception:
        return Response({'error': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)


class UtilisateurListView(generics.ListAPIView):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsStaffOrDFIP]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class UtilisateurDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsStaffOrDFIP]
