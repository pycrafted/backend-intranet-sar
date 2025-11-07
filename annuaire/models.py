from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Department(models.Model):
    """Modèle pour représenter les départements/services de l'entreprise"""
    name = models.CharField(max_length=100, verbose_name="Nom du département")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Employee(models.Model):
    """Modèle pour représenter les employés avec relations hiérarchiques"""
    
    # Informations personnelles
    first_name = models.CharField(max_length=50, verbose_name="Prénom")
    last_name = models.CharField(max_length=50, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Email professionnel")
    
    # Numéros de téléphone
    phone_fixed = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone fixe")
    phone_mobile = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone mobile")
    
    # Informations professionnelles
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees', verbose_name="Département")
    position_title = models.CharField(max_length=100, verbose_name="Titre du poste")
    
    # Informations système
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")
    is_active = models.BooleanField(default=True, verbose_name="Actif", help_text="Désactivé si l'employé n'est plus dans LDAP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        name = self.full_name
        return f"{name} - {self.position_title}" if name else f"Employé {self.id}"
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'employé"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name.strip() if self.first_name else "Sans nom"
    
    @property
    def initials(self):
        """Génère les initiales de l'employé, gère les cas où les noms sont vides"""
        first_init = self.first_name[0].upper() if self.first_name and len(self.first_name) > 0 else ""
        last_init = self.last_name[0].upper() if self.last_name and len(self.last_name) > 0 else ""
        
        if first_init and last_init:
            return f"{first_init}{last_init}"
        elif first_init:
            return f"{first_init}{first_init}"  # Double la première initiale si pas de nom
        elif last_init:
            return f"{last_init}{last_init}"  # Double la dernière initiale si pas de prénom
        else:
            return "?"  # Fallback si les deux sont vides
    


