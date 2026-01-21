"""
Configuration Gunicorn pour la production
"""
import multiprocessing
import os

# Chemin du projet Django
bind = f"0.0.0.0:{os.getenv('GUNICORN_PORT', '8001')}"
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # '-' = stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')   # '-' = stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Process naming
proc_name = 'sar-backend'

# Server socket
backlog = 2048

# Worker processes
preload_app = True
daemon = False

# SSL (si nécessaire)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# User/Group (si nécessaire, décommentez et ajustez)
# user = 'www-data'
# group = 'www-data'

# Temp directory
tmp_upload_dir = None

# Server mechanics
pidfile = os.getenv('GUNICORN_PIDFILE', None)
umask = 0
user = None
group = None

# Performance
# worker_tmp_dir = '/dev/shm'  # Utilise la RAM pour les fichiers temporaires (Linux uniquement)
# Sur Windows, ne pas définir worker_tmp_dir (utilise le répertoire temporaire par défaut)

