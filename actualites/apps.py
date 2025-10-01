from django.apps import AppConfig


class ActualitesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actualites'
    
    def ready(self):
        import actualites.signals