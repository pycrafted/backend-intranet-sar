"""
Configuration Waitress pour la production sur Windows
Waitress est un serveur WSGI pur Python compatible Windows
"""
import os

# Configuration du serveur
host = '0.0.0.0'
port = int(os.getenv('WAITRESS_PORT', '8001'))
threads = int(os.getenv('WAITRESS_THREADS', '4'))
channel_timeout = int(os.getenv('WAITRESS_TIMEOUT', '120'))

# Logging
# Waitress utilise le logging Python standard
# Vous pouvez configurer le logging dans settings.py

# Performance
# Waitress gère automatiquement les threads et les connexions
# Pas besoin de configuration supplémentaire pour Windows



