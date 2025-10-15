from django.db import models
from django.utils.text import slugify
import os
from datetime import datetime


def avatar_upload_path(instance, filename):
    """Génère le chemin d'upload pour les avatars des agents"""
    # Obtenir l'extension du fichier
    ext = filename.split('.')[-1]
    # Créer un nom de fichier unique basé sur l'ID de l'agent et la date
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'avatar_{instance.matricule}_{timestamp}.{ext}'
    # Retourner le chemin complet
    return f'avatars/{filename}'


class Direction(models.Model):
    """Modèle représentant une direction de l'entreprise"""
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nom de la direction",
        help_text="Nom complet de la direction (ex: 'Ressources Humaines')"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="Identifiant unique",
        help_text="Identifiant unique en minuscules pour les filtres (ex: 'rh')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Agent(models.Model):
    """Modèle représentant un agent/employé de l'entreprise"""
    
    first_name = models.CharField(
        max_length=100,
        verbose_name="Prénom"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Nom"
    )
    job_title = models.CharField(
        max_length=200,
        verbose_name="Poste",
        help_text="Poste ou fonction de l'agent"
    )
    position_title = models.CharField(
        max_length=200,
        verbose_name="Titre du poste",
        help_text="Titre officiel du poste",
        default=""
    )
    directions = models.ManyToManyField(
        Direction,
        related_name='agents',
        verbose_name="Directions",
        help_text="Directions auxquelles appartient l'agent"
    )
    email = models.EmailField(
        verbose_name="Email",
        unique=True
    )
    phone_fixed = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone fixe",
        help_text="Numéro de téléphone fixe (optionnel)"
    )
    phone_mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone mobile",
        help_text="Numéro de téléphone mobile (optionnel)"
    )
    matricule = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Matricule",
        help_text="Matricule unique de l'agent"
    )
    position = models.IntegerField(
        default=0,
        verbose_name="ID de position"
    )
    department_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nom du département",
        help_text="Nom du département principal"
    )
    hierarchy_level = models.IntegerField(
        default=1,
        verbose_name="Niveau hiérarchique"
    )
    is_manager = models.BooleanField(
        default=False,
        verbose_name="Est manager"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Est actif"
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Photo de profil de l'agent"
    )
    office_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Localisation du bureau"
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name="Manager",
        help_text="Manager de l'agent (le DG n'a pas de manager)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        """Retourne le nom complet de l'agent"""
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        """Retourne les initiales de l'agent"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement certains champs"""
        # Calculer le niveau hiérarchique basé sur le manager
        if self.manager:
            self.hierarchy_level = self.manager.hierarchy_level + 1
        else:
            self.hierarchy_level = 1
        
        # Définir si c'est un manager
        self.is_manager = self.subordinates.exists()
        
            
        # Synchroniser position_title avec job_title
        if self.job_title and not self.position_title:
            self.position_title = self.job_title
        elif self.position_title and not self.job_title:
            self.job_title = self.position_title
            
        # Définir le département principal
        if not self.department_name and self.directions.exists():
            self.department_name = self.directions.first().name
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.job_title}"