from django.db import models
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
        unique=True,
        verbose_name="Nom de la direction",
        help_text="Nom complet de la direction (ex: 'Ressources Humaines')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ['name']


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
    main_direction = models.ForeignKey(
        Direction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Direction principale",
        help_text="Direction principale de l'agent"
    )
    hierarchy_level = models.IntegerField(
        default=1,
        verbose_name="Niveau hiérarchique"
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Photo de profil de l'agent"
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

    @classmethod
    def rebuild_hierarchy_levels(cls):
        """Reconstruit tous les niveaux hiérarchiques depuis le début"""
        # Trouver tous les DG (agents sans manager)
        dgs = cls.objects.filter(manager__isnull=True)
        
        for dg in dgs:
            # Mettre à jour récursivement à partir de chaque DG
            dg.hierarchy_level = 1
            dg.save(update_fields=['hierarchy_level'])
            dg.update_hierarchy_levels()

    @property
    def full_name(self):
        """Retourne le nom complet de l'agent"""
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        """Retourne les initiales de l'agent"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def calculate_hierarchy_level(self):
        """Calcule le niveau hiérarchique basé sur le manager (n+1)"""
        if self.manager:
            # Le niveau est le niveau du manager + 1
            return self.manager.hierarchy_level + 1
        else:
            # Pas de manager = DG (niveau 1)
            return 1

    def update_hierarchy_levels(self, visited=None):
        """Met à jour récursivement les niveaux hiérarchiques de tous les subordonnés"""
        if visited is None:
            visited = set()
        
        # Éviter les boucles infinies
        if self.id in visited:
            return
        visited.add(self.id)
        
        # Mettre à jour le niveau de cet agent
        self.hierarchy_level = self.calculate_hierarchy_level()
        super().save(update_fields=['hierarchy_level'])
        
        # Mettre à jour récursivement tous les subordonnés
        for subordinate in self.subordinates.all():
            subordinate.update_hierarchy_levels(visited)

    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement certains champs"""
        # Calculer le niveau hiérarchique basé sur le manager
        self.hierarchy_level = self.calculate_hierarchy_level()
        
        # Sauvegarder d'abord pour avoir l'ID
        super().save(*args, **kwargs)
        
        
        # Mettre à jour récursivement les niveaux de tous les subordonnés
        self.update_hierarchy_levels()

    def get_hierarchy_path(self):
        """Retourne le chemin hiérarchique complet (DG > Manager > ... > Agent)"""
        path = [self]
        current = self.manager
        while current:
            path.insert(0, current)
            current = current.manager
        return path

    def get_all_subordinates(self):
        """Retourne tous les subordonnés (directs et indirects)"""
        subordinates = list(self.subordinates.all())
        for subordinate in self.subordinates.all():
            subordinates.extend(subordinate.get_all_subordinates())
        return subordinates

    def get_direct_subordinates(self):
        """Retourne uniquement les subordonnés directs"""
        return self.subordinates.all()

    def is_dg(self):
        """Vérifie si l'agent est le DG (niveau 1)"""
        return self.hierarchy_level == 1 and not self.manager

    def get_hierarchy_info(self):
        """Retourne des informations complètes sur la hiérarchie"""
        return {
            'agent': self.full_name,
            'level': self.hierarchy_level,
            'is_dg': self.is_dg(),
            'manager': self.manager.full_name if self.manager else None,
            'direct_subordinates_count': self.subordinates.count(),
            'all_subordinates_count': len(self.get_all_subordinates()),
            'hierarchy_path': [agent.full_name for agent in self.get_hierarchy_path()]
        }

    def __str__(self):
        return f"{self.full_name} - {self.job_title} (Niveau {self.hierarchy_level})"