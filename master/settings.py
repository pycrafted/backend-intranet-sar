from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# Configuration Email (SMTP Microsoft/Office 365)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.office365.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-sbgp$-92156s&no3gayf7b46=aaif8e%+(z**n6nn1mt+5tl&)')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# ============================================================================
# Configuration des URLs (Backend et Frontend)
BASE_URL = config('BASE_URL')
FRONTEND_URL = config('FRONTEND_URL')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',          
    'corsheaders',         
    'django_filters',       
    'authentication',         
    'actualites',            
    'annuaire',                
    'accueil',             
    'mai',                  
    'documents',             
    'health',                  
    'organigramme',
    'reseau_social',
    'forum',
    'security',
    'metriques',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'master.performance_middleware.PerformanceMiddleware',  # Performance logging
    'master.session_debug_middleware.SessionDebugMiddleware',  # Debug sessions
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'master.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'master.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,  # Réutiliser les connexions pendant 10 minutes
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
# Utilise FRONTEND_URL depuis les variables d'environnement
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=f'{FRONTEND_URL}'
).split(',')

# Configuration CORS pour les cookies de session
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Sécurité : seulement les origines autorisées

# Headers CORS autorisés
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

# Méthodes HTTP autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Configuration pour détecter HTTPS derrière un proxy (IIS/ARR)
# Django détectera automatiquement HTTPS via le header X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Utiliser le header X-Forwarded-Host pour construire les URLs correctes
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Configuration CSRF pour les origines de confiance
# Utilise FRONTEND_URL depuis les variables d'environnement
# Note: 127.0.0.1 peut être ajouté via la variable d'environnement si nécessaire
csrf_origins = config(
    'CSRF_TRUSTED_ORIGINS',
    default=FRONTEND_URL
).split(',')
# S'assurer que les origines HTTPS sont incluses
csrf_origins_list = [origin.strip() for origin in csrf_origins if origin.strip()]
# Ajouter automatiquement le domaine HTTPS si FRONTEND_URL est en HTTPS
if FRONTEND_URL.startswith('https://'):
    if FRONTEND_URL not in csrf_origins_list:
        csrf_origins_list.append(FRONTEND_URL)
# Ajouter sar-intranet.sar.sn si pas déjà présent
if 'https://sar-intranet.sar.sn' not in csrf_origins_list:
    csrf_origins_list.append('https://sar-intranet.sar.sn')
CSRF_TRUSTED_ORIGINS = csrf_origins_list

# Configuration CSRF pour les cookies
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Permettre l'accès depuis JavaScript
# Activer les cookies sécurisés si on est derrière un proxy HTTPS
# Django détectera automatiquement HTTPS via SECURE_PROXY_SSL_HEADER
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)

# Configuration des sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 604800  # 7 jours (604800 secondes = 7 * 24 * 60 * 60)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
# Activer les cookies sécurisés si on est derrière un proxy HTTPS
# Django détectera automatiquement HTTPS via SECURE_PROXY_SSL_HEADER
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_SAVE_EVERY_REQUEST = True  # Sauvegarder la session à chaque requête pour prolonger automatiquement
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Ne pas expirer à la fermeture du navigateur
# SESSION_COOKIE_DOMAIN = None  # Par défaut, le domaine est celui de la requête

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Configuration des fichiers uploadés
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration des fichiers PDF
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Configuration RAG 
RAG_CONFIG = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'VECTOR_DIMENSION': 384,
    'MAX_CONTEXT_LENGTH': 2000,
    'SIMILARITY_THRESHOLD': 0.7,  # Seuil optimisé pour la qualité
    'MAX_DOCUMENTS': 5,
    'CACHE_ENABLED': True,
    'CACHE_TTL': 3600,  # 1 heure
    'BATCH_SIZE': 50,  # Optimisé pour all-MiniLM-L6-v2
    'PERFORMANCE_MODE': True
}

# Configuration Redis 
REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT', cast=int)
REDIS_DB = config('REDIS_DB', cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default=None) 

# Configuration du cache Redis optimisé
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            }
        }
    }
}

# Configuration de migration RAG - Phase 6
RAG_MIGRATION_CONFIG = {
    'ENABLE_VECTOR_SEARCH': True,
    'ENABLE_HEURISTIC_FALLBACK': True,
    'VECTOR_THRESHOLD': 0.7,
    'HEURISTIC_THRESHOLD': 0.2,
    'MIGRATION_PHASE': 'hybrid',  # Migration progressive
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'CACHE_ENABLED': True,
    'CACHE_TTL': 3600,
    'BATCH_SIZE': 50,
    'PERFORMANCE_MODE': True
}

# Configuration des modèles RAG
RAG_EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
RAG_SIMILARITY_THRESHOLD = 0.4  # Seuil abaissé pour trouver plus de résultats
RAG_MAX_DOCUMENTS = 5

# Configuration d'authentification basique Django
AUTH_USER_MODEL = 'authentication.User'
AUTHENTICATION_BACKENDS = [
    'authentication.backends.LDAPBackend',  # Backend LDAP en priorité
    'django.contrib.auth.backends.ModelBackend',  # Fallback pour les comptes locaux
]

# URLs de redirection OAuth
# Utilise FRONTEND_URL depuis les variables d'environnement
LOGIN_REDIRECT_URL = config('LOGIN_REDIRECT_URL', default=f'{FRONTEND_URL}/accueil')
LOGOUT_REDIRECT_URL = config('LOGOUT_REDIRECT_URL', default=f'{FRONTEND_URL}/login')

# Configuration LDAP pour la synchronisation de l'annuaire
LDAP_ENABLED = config('LDAP_ENABLED', default='True', cast=bool)
LDAP_SERVER = config('LDAP_SERVER', default='')
LDAP_PORT = config('LDAP_PORT', default=389, cast=int)
LDAP_BASE_DN = config('LDAP_BASE_DN', default='DC=sar,DC=sn')
LDAP_BIND_DN = config('LDAP_BIND_DN', default='')
LDAP_BIND_PASSWORD = config('LDAP_BIND_PASSWORD', default='')
# Filtre LDAP pour les utilisateurs actifs (exclut les comptes système)
# Modifier ce filtre dans settings.py pour personnaliser les exclusions
LDAP_USER_FILTER = "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(!(sAMAccountName=*$))(!(sAMAccountName=HealthMailbox*))(!(sAMAccountName=IUSR_*))(!(sAMAccountName=IWAM_*))(!(sAMAccountName=MSOL_*))(!(sAMAccountName=AAD_*))(!(sAMAccountName=ASPNET))(!(sAMAccountName=Administrateur))(!(sAMAccountName=docubase))(!(sAMAccountName=sc1adm))(!(sAMAccountName=SAPServiceSC1))(!(sAMAccountName=ISEADMIN))(!(sAMAccountName=user.test.01))(!(sAMAccountName=solarwinds))(!(sAMAccountName=SAC_FTP))(!(sAMAccountName=SQLSERVICE)))"

# ============================================================================
# Configuration Logging pour le debug
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'performance': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Activer le logging SQL en développement pour analyser les requêtes
if DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }

