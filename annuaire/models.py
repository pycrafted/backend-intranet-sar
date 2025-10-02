from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone

User = get_user_model()


class Department(models.Model):
    """Modèle pour représenter les départements/services de l'entreprise"""
    name = models.CharField(max_length=100, verbose_name="Nom du département")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Localisation")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Position(models.Model):
    """Modèle pour représenter les postes/fonctions"""
    title = models.CharField(max_length=100, verbose_name="Titre du poste")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions', verbose_name="Département")
    level = models.IntegerField(default=1, verbose_name="Niveau hiérarchique")
    description = models.TextField(blank=True, null=True, verbose_name="Description du poste")
    is_management = models.BooleanField(default=False, verbose_name="Poste de direction")
    
    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['level', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.department.name}"


class Employee(models.Model):
    """Modèle pour représenter les employés avec relations hiérarchiques"""
    
    # Informations personnelles
    first_name = models.CharField(max_length=50, verbose_name="Prénom")
    last_name = models.CharField(max_length=50, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Email professionnel")
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Format: '+999999999'. Maximum 15 chiffres.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, unique=True, verbose_name="Téléphone")
    
    # Informations professionnelles
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees', verbose_name="Poste")
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates', verbose_name="Supérieur hiérarchique (N+1)")
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Matricule")
    
    # Informations de localisation
    office_location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Bureau")
    work_schedule = models.CharField(max_length=50, default="Temps plein", verbose_name="Horaires de travail")
    
    # Informations système
    user_account = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Compte utilisateur")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    hire_date = models.DateField(default=timezone.now, verbose_name="Date d'embauche")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position.title}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    
    @property
    def hierarchy_level(self):
        """Calcule automatiquement le niveau hiérarchique basé sur le manager"""
        if not self.manager:
            return 1  # CEO ou employé sans manager = niveau 1
        return self.manager.hierarchy_level + 1
    
    @property
    def is_manager(self):
        """Vérifie si l'employé a des subordonnés"""
        return self.subordinates.exists()
    
    def get_all_subordinates(self):
        """Retourne tous les subordonnés (récursif)"""
        subordinates = list(self.subordinates.all())
        for subordinate in subordinates:
            subordinates.extend(subordinate.get_all_subordinates())
        return subordinates
    
    def update_hierarchy_levels(self):
        """Met à jour récursivement les niveaux hiérarchiques de tous les subordonnés"""
        for subordinate in self.subordinates.all():
            # Le niveau sera automatiquement calculé par la propriété hierarchy_level
            subordinate.save()  # Force la sauvegarde pour déclencher les signaux
            subordinate.update_hierarchy_levels()  # Récursion pour les sous-niveaux
    
    def get_management_chain(self):
        """Retourne la chaîne de management jusqu'au sommet"""
        chain = []
        current = self.manager
        while current:
            chain.append(current)
            current = current.manager
        return chain


class OrganizationalChart(models.Model):
    """Modèle pour stocker la configuration de l'organigramme"""
    name = models.CharField(max_length=100, verbose_name="Nom de l'organigramme")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Organigramme"
        verbose_name_plural = "Organigrammes"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


