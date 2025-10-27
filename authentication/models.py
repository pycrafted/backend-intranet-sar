from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour la SAR
    Utilise le modèle User par défaut de Django
    """
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

