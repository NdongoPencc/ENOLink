from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'cga-service-secret-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')
CORE_SERVICE_URL = os.getenv('CORE_SERVICE_URL', 'http://localhost:8002')

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'algorithm',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'cga_service.urls'

TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
               'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': []}}]

DATABASES = {}  # Le CGA-service ne stocke rien, il délègue au core-service

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['cga_service.auth.RemoteJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

SIMPLE_JWT = {
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('SECRET_KEY', 'auth-service-secret-key-enolink-2026'),
}

CORS_ALLOWED_ORIGINS = ['http://localhost:4200', 'http://localhost:8000']
STATIC_URL = '/static/'
