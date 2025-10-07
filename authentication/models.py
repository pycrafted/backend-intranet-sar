from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour la SAR
    Version simplifiée - seulement les champs essentiels
    """
    
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Photo de profil de l'utilisateur"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numéro de téléphone personnel de l'utilisateur"
    )
    
    office_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numéro de téléphone fixe du bureau de l'utilisateur"
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Poste occupé par l'utilisateur dans l'entreprise"
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Département de l'utilisateur dans l'entreprise"
    )
    
    matricule = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Matricule unique de l'utilisateur dans l'entreprise"
    )
    
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        help_text="Chef direct (N+1) de l'utilisateur"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si le compte est actif"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du compte"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    # Champs OAuth Google
    google_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="ID Google unique de l'utilisateur"
    )
    
    google_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email Google de l'utilisateur"
    )
    
    google_avatar_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de l'avatar Google de l'utilisateur"
    )
    
    google_access_token = models.TextField(
        blank=True,
        null=True,
        help_text="Token d'accès Google (chiffré)"
    )
    
    google_refresh_token = models.TextField(
        blank=True,
        null=True,
        help_text="Token de rafraîchissement Google (chiffré)"
    )
    
    google_token_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date d'expiration du token Google"
    )
    
    # Métadonnées
    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retourne le prénom de l'utilisateur"""
        return self.first_name
    
    def is_google_connected(self):
        """Vérifie si l'utilisateur est connecté via Google"""
        return bool(self.google_id and self.google_access_token)
    
    def get_google_avatar_url(self):
        """Retourne l'URL de l'avatar Google ou None"""
        return self.google_avatar_url
    
    def get_google_display_name(self):
        """Retourne le nom d'affichage Google"""
        if self.google_email:
            return self.google_email.split('@')[0]
        return self.get_full_name()
