"""
Configuration spécifique pour Render.
Optimisée pour le déploiement cloud sans chemins absolus.
"""
import os
from decouple import config
from .settings import *

# ========================================
# CONFIGURATION RENDER
# ========================================

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

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
# BASE DE DONNÉES RENDER
# ========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='sar_production'),
        'USER': config('POSTGRES_USER', default='sar_user'),
        'PASSWORD': config('POSTGRES_PASSWORD', default=''),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 30,
            'options': '-c default_transaction_isolation="read committed"'
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
        'CONN_HEALTH_CHECKS': True,
    }
}

# ========================================
# CACHE RENDER (DÉSACTIVÉ - PAS DE REDIS)
# ========================================

# Redis non disponible sur Render - Utilisation du cache local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sar_rag_cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        },
        'TIMEOUT': 300,  # 5 minutes
        'VERSION': 1,
        'KEY_PREFIX': 'sar_rag',
    }
}

# Configuration Redis désactivée pour Render
USE_REDIS = False
REDIS_AVAILABLE = False

# ========================================
# CONFIGURATION RAG RENDER
# ========================================

RAG_CONFIG = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'VECTOR_DIMENSION': 384,
    'MAX_CONTEXT_LENGTH': 2000,
    'SIMILARITY_THRESHOLD': 0.7,
    'MAX_DOCUMENTS': 5,
    'CACHE_ENABLED': False,  # Désactivé sur Render (pas de Redis)
    'CACHE_TTL': 3600,  # 1 heure
    'BATCH_SIZE': 50,  # Réduit pour Render
    'PERFORMANCE_MODE': True,
    'ENABLE_MONITORING': True,
    'LOG_LEVEL': 'INFO',
    'MAX_CONCURRENT_REQUESTS': 50,  # Réduit pour Render
    'RATE_LIMIT_PER_MINUTE': 500,  # Réduit pour Render
}

# Configuration de migration progressive
RAG_MIGRATION_CONFIG = {
    'ENABLE_VECTOR_SEARCH': True,
    'ENABLE_HEURISTIC_FALLBACK': True,
    'VECTOR_THRESHOLD': 0.7,
    'HEURISTIC_THRESHOLD': 0.2,
    'MIGRATION_PHASE': 'production',  # Phase production
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'CACHE_ENABLED': False,  # Désactivé sur Render (pas de Redis)
    'CACHE_TTL': 3600,
    'BATCH_SIZE': 50,  # Réduit pour Render
    'PERFORMANCE_MODE': True,
    'MONITORING_ENABLED': True,
    'AUTO_OPTIMIZATION': False,  # Désactivé sur Render
    'OPTIMIZATION_INTERVAL_HOURS': 24,
}

# ========================================
# LOGGING RENDER (CONSOLE UNIQUEMENT)
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
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

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
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Middleware Allauth REQUIS
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

# Configuration du cache vectoriel (désactivé sur Render)
VECTOR_CACHE_CONFIG = {
    'enabled': False,  # Désactivé sur Render (pas de Redis)
    'max_size': 1000,  # Réduit pour Render
    'ttl': 3600,  # 1 heure
    'compression': True,
}

# Configuration de l'optimisation automatique (désactivée sur Render)
AUTO_OPTIMIZATION_CONFIG = {
    'enabled': False,  # Désactivé sur Render
    'schedule': '0 2 * * *',  # Tous les jours à 2h du matin
    'max_duration_minutes': 30,
    'performance_threshold': 0.8,
}

# ========================================
# CONFIGURATION DE DÉPLOIEMENT
# ========================================

# Variables d'environnement de production
PRODUCTION = True
ENVIRONMENT = 'render'

# Configuration des workers
WSGI_APPLICATION = 'master.wsgi.application'

# Configuration des timeouts
REQUEST_TIMEOUT = 30
RESPONSE_TIMEOUT = 60

# Configuration de la mémoire
MAX_MEMORY_USAGE = 0.8  # 80% de la RAM disponible

# ========================================
# CONFIGURATION DE SAUVEGARDE (DÉSACTIVÉE)
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

print("Configuration Render chargée avec succès!")
