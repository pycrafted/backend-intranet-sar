"""
Configuration de production pour le système RAG SAR.
Optimisée pour la performance, la sécurité et la scalabilité.
"""
import os
from decouple import config
from .settings import *

# ========================================
# CONFIGURATION DE PRODUCTION
# ========================================

DEBUG = False
# ============================================================================
# ALLOWED_HOSTS
# ============================================================================
# ⚠️ SÉCURITÉ : Doit être défini dans le fichier .env
# Format: host1,host2,host3 (séparés par des virgules)
# ============================================================================
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# ========================================
# SÉCURITÉ RENFORCÉE
# ========================================

# Configuration CORS pour production
CORS_ALLOWED_ORIGINS = [
    "https://frontend-intranet-sar-1.onrender.com",
    "https://intranet-sar.com",
    "https://www.intranet-sar.com",
]

CORS_ALLOW_CREDENTIALS = True

# Configuration CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://frontend-intranet-sar-1.onrender.com",
    "https://intranet-sar.com",
    "https://www.intranet-sar.com",
]

# Sécurité des cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ========================================
# BASE DE DONNÉES PRODUCTION
# ========================================
# ⚠️ SÉCURITÉ : Tous les paramètres DOIVENT être définis dans le fichier .env
# Aucune valeur par défaut dans le code pour éviter l'exposition de secrets
# ========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 30,
            'options': '-c default_transaction_isolation=read_committed'
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
        'CONN_HEALTH_CHECKS': True,
    }
}

# ========================================
# CACHE REDIS PRODUCTION
# ========================================

# ============================================================================
# Configuration Redis pour Production
# ============================================================================
# ⚠️ SÉCURITÉ : Tous les paramètres DOIVENT être définis dans le fichier .env
# ============================================================================
REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT', cast=int)
REDIS_DB = config('REDIS_DB', cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default=None)  # Peut être vide

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'TIMEOUT': 300,  # 5 minutes
        'VERSION': 1,
        'KEY_PREFIX': 'sar_rag',
    }
}

# ========================================
# CONFIGURATION RAG PRODUCTION
# ========================================

RAG_CONFIG = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'VECTOR_DIMENSION': 384,
    'MAX_CONTEXT_LENGTH': 2000,
    'SIMILARITY_THRESHOLD': 0.7,
    'MAX_DOCUMENTS': 5,
    'CACHE_ENABLED': True,
    'CACHE_TTL': 3600,  # 1 heure
    'BATCH_SIZE': 100,  # Optimisé pour production
    'PERFORMANCE_MODE': True,
    'ENABLE_MONITORING': True,
    'LOG_LEVEL': 'INFO',
    'MAX_CONCURRENT_REQUESTS': 100,
    'RATE_LIMIT_PER_MINUTE': 1000,
}

# Configuration de migration progressive
RAG_MIGRATION_CONFIG = {
    'ENABLE_VECTOR_SEARCH': True,
    'ENABLE_HEURISTIC_FALLBACK': True,
    'VECTOR_THRESHOLD': 0.7,
    'HEURISTIC_THRESHOLD': 0.2,
    'MIGRATION_PHASE': 'production',  # Phase production
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'CACHE_ENABLED': True,
    'CACHE_TTL': 3600,
    'BATCH_SIZE': 100,
    'PERFORMANCE_MODE': True,
    'MONITORING_ENABLED': True,
    'AUTO_OPTIMIZATION': True,
    'OPTIMIZATION_INTERVAL_HOURS': 24,
}

# ========================================
# LOGGING PRODUCTION (RENDER COMPATIBLE)
# ========================================

# Configuration de logging compatible avec Render - CONSOLE UNIQUEMENT
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'mai': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# ========================================
# SÉCURITÉ SUPPLÉMENTAIRE
# ========================================

# Configuration de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuration des sessions
SESSION_COOKIE_AGE = 604800  # 7 jours (604800 secondes = 7 * 24 * 60 * 60)
SESSION_SAVE_EVERY_REQUEST = True  # Sauvegarder à chaque requête pour prolonger la session
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Ne pas expirer à la fermeture du navigateur
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# ========================================
# PERFORMANCE ET OPTIMISATION
# ========================================

# Configuration des fichiers statiques (Render compatible)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration de la base de données
DATABASE_ROUTERS = []

# Configuration des middlewares optimisés
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================================
# MONITORING ET MÉTRIQUES
# ========================================

# Configuration des métriques
ENABLE_METRICS = True
METRICS_INTERVAL = 60  # secondes
HEALTH_CHECK_INTERVAL = 30  # secondes

# Configuration des alertes
ALERT_EMAIL = config('ALERT_EMAIL', default='admin@intranet-sar.com')
ALERT_SLACK_WEBHOOK = config('ALERT_SLACK_WEBHOOK', default=None)

# ========================================
# CONFIGURATION SPÉCIFIQUE RAG
# ========================================

# Configuration des modèles d'embedding (Render compatible)
EMBEDDING_MODEL_CONFIG = {
    'model_name': 'all-MiniLM-L6-v2',
    'cache_dir': os.path.join(BASE_DIR, 'cache', 'models'),
    'max_sequence_length': 512,
    'batch_size': 100,
    'device': 'cpu',  # ou 'cuda' si GPU disponible
}

# Configuration du cache vectoriel
VECTOR_CACHE_CONFIG = {
    'enabled': True,
    'max_size': 10000,  # nombre max d'embeddings en cache
    'ttl': 3600,  # 1 heure
    'compression': True,
}

# Configuration de l'optimisation automatique
AUTO_OPTIMIZATION_CONFIG = {
    'enabled': True,
    'schedule': '0 2 * * *',  # Tous les jours à 2h du matin
    'max_duration_minutes': 30,
    'performance_threshold': 0.8,
}

# ========================================
# CONFIGURATION DE DÉPLOIEMENT
# ========================================

# Variables d'environnement de production
PRODUCTION = True
ENVIRONMENT = 'production'

# Configuration des workers
WSGI_APPLICATION = 'master.wsgi.application'

# Configuration des timeouts
REQUEST_TIMEOUT = 30
RESPONSE_TIMEOUT = 60

# Configuration de la mémoire
MAX_MEMORY_USAGE = 0.8  # 80% de la RAM disponible

# ========================================
# CONFIGURATION DE SAUVEGARDE
# ========================================

BACKUP_CONFIG = {
    'enabled': False,  # Désactivé sur Render
    'schedule': '0 1 * * *',  # Tous les jours à 1h du matin
    'retention_days': 30,
    'backup_dir': os.path.join(BASE_DIR, 'backups'),
    'include_media': True,
    'include_static': True,
}

# ========================================
# CONFIGURATION DE ROLLBACK
# ========================================

ROLLBACK_CONFIG = {
    'enabled': True,
    'max_versions': 5,
    'auto_rollback_threshold': 0.1,  # 10% d'erreurs
    'rollback_check_interval': 300,  # 5 minutes
}

print("Configuration de production chargée avec succès!")