from django.apps import AppConfig


class ReseauSocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reseau_social'
    
    def ready(self):
        import reseau_social.signals  # noqa