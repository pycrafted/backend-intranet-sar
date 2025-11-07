from django.db import models
from django.utils import timezone
from datetime import datetime, date, timedelta


class Department(models.Model):
    """
    Modèle pour gérer les départements de l'entreprise
    Chaque département peut avoir plusieurs emails associés pour l'envoi groupé
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Code unique du département (ex: 'production', 'maintenance')"
    )
    name = models.CharField(
        max_length=100,
        help_text="Nom complet du département (ex: 'Production', 'Maintenance')"
    )
    emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des emails associés au département pour l'envoi groupé"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si le département est actif"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_emails_list(self):
        """
        Retourne la liste des emails valides du département
        """
        if not self.emails:
            return []
        # Filtrer les emails vides ou invalides
        return [email for email in self.emails if email and '@' in email]


class Idea(models.Model):
    """
    Modèle pour gérer les idées soumises via la boîte à idées
    """
    STATUS_CHOICES = [
        ('submitted', 'Soumise'),
        ('under_review', 'En cours d\'examen'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
        ('implemented', 'Implémentée'),
    ]
    
    # Champs principaux
    description = models.TextField(
        help_text="Description détaillée de l'idée"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='ideas',
        help_text="Département concerné par l'idée"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        help_text="Statut actuel de l'idée"
    )
    
    # Métadonnées
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Idée"
        verbose_name_plural = "Idées"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Idée #{self.id} - {self.department.name} - {self.get_status_display()}"


class SafetyData(models.Model):
    """
    Modèle pour gérer les données de sécurité du travail
    """
    # Dates des derniers accidents
    last_incident_date_sar = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date du dernier accident SAR (interne)"
    )
    last_incident_date_ee = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date du dernier accident EE (externe)"
    )
    
    # Détails des derniers accidents
    last_incident_type_sar = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type du dernier accident SAR"
    )
    last_incident_type_ee = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type du dernier accident EE"
    )
    last_incident_description_sar = models.TextField(
        blank=True,
        help_text="Description du dernier accident SAR"
    )
    last_incident_description_ee = models.TextField(
        blank=True,
        help_text="Description du dernier accident EE"
    )
    
    # Score de sécurité (calculé)
    safety_score = models.PositiveIntegerField(
        default=0,
        help_text="Score de sécurité global (0-100)"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Données de Sécurité"
        verbose_name_plural = "Données de Sécurité"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Sécurité - SAR: {self.days_without_incident_sar}j, EE: {self.days_without_incident_ee}j"
    
    @property
    def days_without_incident_sar(self):
        """Calcule le nombre de jours sans accident SAR depuis la dernière date d'accident"""
        if not self.last_incident_date_sar:
            # Si jamais d'accident, calculer depuis la création
            return (timezone.now() - self.created_at).days
        return (timezone.now() - self.last_incident_date_sar).days
    
    @property
    def days_without_incident_ee(self):
        """Calcule le nombre de jours sans accident EE depuis la dernière date d'accident"""
        if not self.last_incident_date_ee:
            # Si jamais d'accident, calculer depuis la création
            return (timezone.now() - self.created_at).days
        return (timezone.now() - self.last_incident_date_ee).days
    
    @property
    def days_without_incident(self):
        """Retourne le minimum entre SAR et EE"""
        return min(self.days_without_incident_sar, self.days_without_incident_ee)
    
    @property
    def last_incident_date(self):
        """Retourne la date du dernier accident (SAR ou EE)"""
        if not self.last_incident_date_sar and not self.last_incident_date_ee:
            return None
        if not self.last_incident_date_sar:
            return self.last_incident_date_ee
        if not self.last_incident_date_ee:
            return self.last_incident_date_sar
        return max(self.last_incident_date_sar, self.last_incident_date_ee)
    
    @property
    def last_incident_type(self):
        """Retourne le type du dernier accident"""
        if not self.last_incident_date:
            return None
        if self.last_incident_date == self.last_incident_date_sar:
            return self.last_incident_type_sar
        return self.last_incident_type_ee
    
    @property
    def last_incident_description(self):
        """Retourne la description du dernier accident"""
        if not self.last_incident_date:
            return None
        if self.last_incident_date == self.last_incident_date_sar:
            return self.last_incident_description_sar
        return self.last_incident_description_ee
    
    def get_appreciation(self, days_count):
        """Retourne une appréciation basée sur le nombre de jours"""
        if days_count >= 365:
            return "Excellent"
        elif days_count >= 180:
            return "Très bien"
        elif days_count >= 90:
            return "Bien"
        elif days_count >= 30:
            return "Correct"
        elif days_count >= 7:
            return "À améliorer"
        else:
            return "Attention"
    
    @property
    def appreciation_sar(self):
        """Appréciation pour SAR"""
        return self.get_appreciation(self.days_without_incident_sar)
    
    @property
    def appreciation_ee(self):
        """Appréciation pour EE"""
        return self.get_appreciation(self.days_without_incident_ee)
    
    def update_safety_score(self):
        """Met à jour le score de sécurité basé sur les jours sans accident"""
        sar_days = self.days_without_incident_sar
        ee_days = self.days_without_incident_ee
        
        # Score basé sur le minimum des deux
        min_days = min(sar_days, ee_days)
        
        if min_days >= 365:
            self.safety_score = 100
        elif min_days >= 180:
            self.safety_score = 90
        elif min_days >= 90:
            self.safety_score = 80
        elif min_days >= 30:
            self.safety_score = 70
        elif min_days >= 7:
            self.safety_score = 60
        else:
            self.safety_score = 50
        
        self.save(update_fields=['safety_score'])
        return self.safety_score


class MenuItem(models.Model):
    """
    Modèle pour les plats du menu
    """
    TYPE_CHOICES = [
        ('senegalese', 'Sénégalais'),
        ('european', 'Européen'),
    ]
    
    name = models.CharField(
        max_length=200,
        help_text="Nom du plat"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type de cuisine"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description du plat"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Disponibilité du plat"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plat"
        verbose_name_plural = "Plats"
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class DayMenu(models.Model):
    """
    Modèle pour le menu d'un jour de la semaine
    """
    DAY_CHOICES = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ]
    
    day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        help_text="Jour de la semaine"
    )
    date = models.DateField(
        help_text="Date du menu"
    )
    senegalese = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='senegalese_menus',
        limit_choices_to={'type': 'senegalese'},
        help_text="Plat sénégalais du jour"
    )
    european = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='european_menus',
        limit_choices_to={'type': 'european'},
        help_text="Plat européen du jour"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Menu actif ou non"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Menu du Jour"
        verbose_name_plural = "Menus des Jours"
        ordering = ['date', 'day']
        unique_together = ['day', 'date']
    
    def __str__(self):
        return f"{self.get_day_display()} {self.date} - {self.senegalese.name} / {self.european.name}"


class Event(models.Model):
    """
    Modèle pour gérer les événements de l'entreprise
    """
    TYPE_CHOICES = [
        ('meeting', 'Réunion'),
        ('training', 'Formation'),
        ('celebration', 'Célébration'),
        ('conference', 'Conférence'),
        ('other', 'Autre'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre de l'événement",
        help_text="Titre court et descriptif de l'événement"
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Description détaillée de l'événement",
        blank=True
    )
    date = models.DateField(
        verbose_name="Date",
        help_text="Date de l'événement"
    )
    time = models.TimeField(
        verbose_name="Heure",
        help_text="Heure de début de l'événement",
        null=True,
        blank=True
    )
    location = models.CharField(
        max_length=200,
        verbose_name="Lieu",
        help_text="Lieu où se déroule l'événement"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='other',
        verbose_name="Type d'événement",
        help_text="Catégorie de l'événement"
    )
    attendees = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de participants",
        help_text="Nombre estimé de participants"
    )
    is_all_day = models.BooleanField(
        default=False,
        verbose_name="Toute la journée",
        help_text="Cochez si l'événement dure toute la journée"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['type']),
            models.Index(fields=['is_all_day']),
        ]
    
    def __str__(self):
        time_str = f" à {self.time.strftime('%H:%M')}" if self.time else ""
        return f"{self.title} - {self.date}{time_str}"
    
    @property
    def is_past(self):
        """Vérifie si l'événement est dans le passé"""
        if not self.date:
            return False
        
        today = timezone.now().date()
        if self.is_all_day:
            return self.date < today
        else:
            # Pour les événements avec heure, on compare la date et l'heure
            event_datetime = timezone.datetime.combine(self.date, self.time or timezone.datetime.min.time())
            return event_datetime.date() < today
    
    @property
    def is_today(self):
        """Vérifie si l'événement est aujourd'hui"""
        if not self.date:
            return False
        return self.date == timezone.now().date()
    
    @property
    def is_future(self):
        """Vérifie si l'événement est dans le futur"""
        return not self.is_past and not self.is_today

