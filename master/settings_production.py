"""
Configuration de production pour le déploiement sur Render
Basée sur settings.py mais optimisée pour la production
"""

from .settings import *
import os
from decouple import config

# =============================================================================
# SÉCURITÉ - Configuration critique pour la production
# =============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY est obligatoire en production")

# Hosts autorisés - Render fournit l'URL via RENDER_EXTERNAL_HOSTNAME
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    config('RENDER_EXTERNAL_HOSTNAME', default=''),
    config('FRONTEND_URL', default='').replace('https://', '').replace('http://', ''),
]

# Nettoyer les hosts vides
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host]

# =============================================================================
# BASE DE DONNÉES - Configuration Render PostgreSQL
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default=''),
        'USER': config('POSTGRES_USER', default=''),
        'PASSWORD': config('POSTGRES_PASSWORD', default=''),
        'HOST': config('POSTGRES_HOST', default=''),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',  # SSL obligatoire sur Render
        }
    }
}

# Vérifier que la configuration DB est complète
required_db_vars = ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST']
missing_vars = [var for var in required_db_vars if not config(var, default='')]
if missing_vars:
    raise ValueError(f"Variables de base de données manquantes: {missing_vars}")

# =============================================================================
# FICHIERS STATIQUES - Configuration pour Render
# =============================================================================

# Chemin vers les fichiers statiques
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuration WhiteNoise pour servir les fichiers statiques
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configuration des fichiers statiques
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration des fichiers média (optionnel - utiliser un service externe en production)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
# CORS - Configuration pour le frontend
# =============================================================================

# URL du frontend (peut être sur Render ou ailleurs)
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",  # Fallback pour le développement
    "https://frontend-intranet-ndpvti2al-abdoulaye-lahs-projects.vercel.app",  # URL Vercel 1
    "https://frontend-intranet-jjg1gmzmr-abdoulaye-lahs-projects.vercel.app",  # URL Vercel 2
    "https://frontend-intranet-h6yicbrwg-abdoulaye-lahs-projects.vercel.app",  # URL Vercel 3
    "https://frontend-intranet-8fufyhe3w-abdoulaye-lahs-projects.vercel.app",  # URL Vercel actuelle
    "https://frontend-intranet-sar.vercel.app",  # URL Vercel de base
]

# Accepter toutes les URLs Vercel (pattern wildcard)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://frontend-intranet.*\.vercel\.app$",
    r"^https://.*\.vercel\.app$",  # Accepter toutes les URLs Vercel
]

# Nettoyer les URLs vides
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin]

# Configuration CORS pour les cookies de session
CORS_ALLOW_CREDENTIALS = True  # Activé pour les endpoints qui nécessitent l'authentification
CORS_ALLOW_ALL_ORIGINS = False  # Sécurité : seulement les origines autorisées

# Headers CORS autorisés pour les images
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Méthodes CORS autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# =============================================================================
# CSRF - Configuration de sécurité
# =============================================================================

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# Configuration CSRF pour les cookies
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Permettre l'accès depuis JavaScript
CSRF_COOKIE_SECURE = True  # HTTPS en production

# =============================================================================
# SESSIONS - Configuration de sécurité
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 heures
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # HTTPS en production
SESSION_SAVE_EVERY_REQUEST = True

# =============================================================================
# SÉCURITÉ HTTPS - Configuration pour production
# =============================================================================

# Redirection HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Headers de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# LOGGING - Configuration des logs pour production
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sar': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================================================
# CACHE - Configuration du cache pour production
# =============================================================================

# Cache simple en mémoire (peut être amélioré avec Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# =============================================================================
# PERFORMANCE - Optimisations pour production
# =============================================================================

# Configuration des connexions DB
DATABASES['default']['CONN_MAX_AGE'] = 60

# Configuration des fichiers uploadés
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# =============================================================================
# RAG - Configuration optimisée pour production
# =============================================================================

# Configuration RAG optimisée pour Render
RAG_CONFIG = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'VECTOR_DIMENSION': 384,
    'MAX_CONTEXT_LENGTH': 2000,
    'SIMILARITY_THRESHOLD': 0.4,
    'MAX_DOCUMENTS': 5,
    'CACHE_EMBEDDINGS': True,  # Mise en cache des embeddings
}

# Configuration des modèles RAG
RAG_EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
RAG_SIMILARITY_THRESHOLD = 0.4
RAG_MAX_DOCUMENTS = 5

# =============================================================================
# OAuth Google - Configuration pour production
# =============================================================================

# Configuration des variables d'environnement OAuth
GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')

# URLs de redirection OAuth pour production
LOGIN_REDIRECT_URL = f'{FRONTEND_URL}/accueil'
LOGOUT_REDIRECT_URL = f'{FRONTEND_URL}/login'

# =============================================================================
# CLAUDE API - Configuration pour le RAG
# =============================================================================

CLAUDE_API_KEY = config('CLAUDE_API_KEY', default='')

if not CLAUDE_API_KEY:
    print("⚠️  CLAUDE_API_KEY non définie - Le système RAG ne fonctionnera pas")

# =============================================================================
# RENDER SPECIFIC - Configuration spécifique à Render
# =============================================================================

# URL de base pour les médias
BASE_URL = config('BASE_URL', default='https://backend-intranet-sar-1.onrender.com')

# Port pour Render (fourni via la variable d'environnement PORT)
PORT = config('PORT', default='8000', cast=int)

# Configuration pour les workers Gunicorn
WORKERS = config('WORKERS', default=2, cast=int)

# =============================================================================
# VALIDATION - Vérifications finales
# =============================================================================

def validate_production_config():
    """Valide la configuration de production"""
    errors = []
    
    if DEBUG:
        errors.append("DEBUG doit être False en production")
    
    if not SECRET_KEY or len(SECRET_KEY) < 50:
        errors.append("SECRET_KEY doit être définie et sécurisée (minimum 50 caractères)")
    
    if not ALLOWED_HOSTS:
        errors.append("ALLOWED_HOSTS doit contenir au moins un host")
    
    if errors:
        raise ValueError(f"Configuration de production invalide: {'; '.join(errors)}")

# Valider la configuration au chargement
validate_production_config()

print("✅ Configuration de production chargée avec succès")
