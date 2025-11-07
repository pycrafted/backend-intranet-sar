from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour la SAR
    Utilise le modèle User par défaut de Django
    TOUS les comptes sont toujours actifs par défaut
    """
    matricule = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Matricule",
        help_text="Matricule unique de l'utilisateur"
    )
    
    phone_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Téléphone personnel",
        help_text="Numéro de téléphone personnel"
    )
    
    phone_fixed = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Téléphone fixe",
        help_text="Numéro de téléphone fixe (bureau)"
    )
    
    department = models.ForeignKey(
        'annuaire.Department',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Département",
        help_text="Département de l'utilisateur",
        related_name='users'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/users/',
        blank=True,
        null=True,
        verbose_name="Photo de profil",
        help_text="Photo de profil de l'utilisateur"
    )
    
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='subordinates',
        verbose_name="Manager (N+1)",
        help_text="Supérieur hiérarchique de l'utilisateur"
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Poste occupé",
        help_text="Poste occupé par l'utilisateur (ex: DG, DSI, Comptable, Développeur)"
    )
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour forcer is_active=True
        Tous les comptes sont toujours actifs
        """
        # TOUJOURS activer le compte, que ce soit une création ou une mise à jour
        self.is_active = True
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

