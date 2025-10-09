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
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Matricule")
    
    # Informations système
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position_title}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    


