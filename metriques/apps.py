from django.apps import AppConfig


class MetriquesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'metriques'
    
    def ready(self):
        import metriques.signals  # noqa