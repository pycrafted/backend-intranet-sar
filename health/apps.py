"""
Configuration de l'application health.
"""
from django.apps import AppConfig

class HealthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'health'

