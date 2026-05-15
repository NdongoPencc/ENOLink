"""
Authentification inter-services : valide le JWT auprès du auth-service.
Injecte un utilisateur proxy dans request.user.
"""
import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class RemoteUser:
    """Utilisateur proxy reconstruit depuis la réponse du auth-service."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.email = data.get('email')
        self.nom = data.get('nom')
        self.prenom = data.get('prenom')
        self.role = data.get('role')
        self.is_authenticated = True
        self.is_active = True

    @property
    def is_dfip(self): return self.role == 'DFIP'
    @property
    def is_enseignant(self): return self.role == 'ENSEIGNANT'
    @property
    def is_coordinateur(self): return self.role == 'COORDINATEUR'
    @property
    def is_apprenant(self): return self.role == 'APPRENANT'


class RemoteJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1]
        try:
            resp = requests.get(
                f"{settings.AUTH_SERVICE_URL}/api/auth/profil/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=3,
            )
            if resp.status_code != 200:
                raise AuthenticationFailed('Token invalide ou expiré.')
            return (RemoteUser(resp.json()), token)
        except requests.RequestException:
            raise AuthenticationFailed('Auth-service inaccessible.')
