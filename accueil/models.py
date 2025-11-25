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
        """
        Calcule le nombre de jours sans accident SAR depuis la dernière date d'accident.
        Compare les dates (sans l'heure) pour que le compteur s'incrémente à minuit.
        Utilise un calcul basé sur les jours calendaires pour garantir une incrémentation correcte à minuit.
        """
        # Obtenir la date d'aujourd'hui dans le fuseau horaire local (UTC par défaut)
        now = timezone.now()
        today = now.date()
        
        if not self.last_incident_date_sar:
            # Si jamais d'accident, calculer depuis la création
            if isinstance(self.created_at, datetime):
                created_date = self.created_at.date()
            else:
                created_date = self.created_at if isinstance(self.created_at, date) else self.created_at.date()
            
            # Calculer la différence en jours calendaires
            delta = today - created_date
            return max(0, delta.days)
        
        # Extraire seulement la date (sans l'heure) pour la comparaison
        if isinstance(self.last_incident_date_sar, datetime):
            incident_date = self.last_incident_date_sar.date()
        elif isinstance(self.last_incident_date_sar, date):
            incident_date = self.last_incident_date_sar
        else:
            # Si c'est une chaîne ou autre format, essayer de convertir
            incident_date = self.last_incident_date_sar
        
        # Calculer la différence en jours calendaires
        # Cette méthode garantit que le compteur s'incrémente correctement à minuit
        delta = today - incident_date
        days = max(0, delta.days)
        
        return days
    
    @property
    def days_without_incident_ee(self):
        """
        Calcule le nombre de jours sans accident EE depuis la dernière date d'accident.
        Compare les dates (sans l'heure) pour que le compteur s'incrémente à minuit.
        Utilise un calcul basé sur les jours calendaires pour garantir une incrémentation correcte à minuit.
        """
        # Obtenir la date d'aujourd'hui dans le fuseau horaire local (UTC par défaut)
        now = timezone.now()
        today = now.date()
        
        if not self.last_incident_date_ee:
            # Si jamais d'accident, calculer depuis la création
            if isinstance(self.created_at, datetime):
                created_date = self.created_at.date()
            else:
                created_date = self.created_at if isinstance(self.created_at, date) else self.created_at.date()
            
            # Calculer la différence en jours calendaires
            delta = today - created_date
            return max(0, delta.days)
        
        # Extraire seulement la date (sans l'heure) pour la comparaison
        if isinstance(self.last_incident_date_ee, datetime):
            incident_date = self.last_incident_date_ee.date()
        elif isinstance(self.last_incident_date_ee, date):
            incident_date = self.last_incident_date_ee
        else:
            # Si c'est une chaîne ou autre format, essayer de convertir
            incident_date = self.last_incident_date_ee
        
        # Calculer la différence en jours calendaires
        # Cette méthode garantit que le compteur s'incrémente correctement à minuit
        delta = today - incident_date
        days = max(0, delta.days)
        
        return days
    
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
        ('dessert', 'Dessert'),
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
    Les plats sont maintenant des champs texte directement dans le menu
    """
    DAY_CHOICES = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
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
    senegalese = models.CharField(
        max_length=200,
        help_text="Nom du plat sénégalais du jour",
        blank=True,
        null=True
    )
    european = models.CharField(
        max_length=200,
        help_text="Nom du plat européen du jour",
        blank=True,
        null=True
    )
    dessert = models.CharField(
        max_length=200,
        help_text="Nom du dessert du jour",
        blank=True,
        null=True
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
        senegalese_name = self.senegalese or "Non renseigné"
        european_name = self.european or "Non renseigné"
        return f"{self.get_day_display()} {self.date} - {senegalese_name} / {european_name}"


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


class Project(models.Model):
    """
    Modèle pour gérer les projets stratégiques
    Tous les champs sont optionnels pour permettre une flexibilité maximale
    """
    STATUS_CHOICES = [
        ('en_cours', 'Études en cours'),
        ('termine', 'Terminé'),
        ('planifie', 'Planifié'),
        ('en_projet', 'En projet'),
    ]
    
    # Informations de base
    titre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Titre du projet"
    )
    objective = models.TextField(
        blank=True,
        null=True,
        help_text="Objectif du projet"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description détaillée du projet"
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Statut actuel du projet"
    )
    date_debut = models.DateField(
        blank=True,
        null=True,
        help_text="Date de début du projet"
    )
    date_fin = models.DateField(
        blank=True,
        null=True,
        help_text="Date de fin prévue du projet"
    )
    
    # Partenaires
    partners = models.TextField(
        blank=True,
        null=True,
        help_text="Partenaires du projet"
    )
    
    # Responsable
    chef_projet = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Chef de projet"
    )
    
    # Image
    image = models.ImageField(
        upload_to='projects/',
        blank=True,
        null=True,
        help_text="Image du projet"
    )
    
    # Métadonnées (cachées dans l'admin mais conservées pour l'historique)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.titre or f"Projet #{self.id}"
    
    @property
    def duration_days(self):
        """Calcule la durée du projet en jours"""
        if not self.date_debut or not self.date_fin:
            return None
        delta = self.date_fin - self.date_debut
        return delta.days
    
    @property
    def duration_formatted(self):
        """Retourne la durée formatée (ex: '2 ans et 3 mois')"""
        if not self.date_debut or not self.date_fin:
            return None
        
        delta = self.date_fin - self.date_debut
        days = delta.days
        
        years = days // 365
        months = (days % 365) // 30
        
        if years > 0 and months > 0:
            return f"{years} an{'s' if years > 1 else ''} et {months} mois"
        elif years > 0:
            return f"{years} an{'s' if years > 1 else ''}"
        elif months > 0:
            return f"{months} mois"
        else:
            return f"{days} jour{'s' if days > 1 else ''}"
    
    # Propriété pour compatibilité avec l'ancien champ 'name'
    @property
    def name(self):
        """Alias pour titre (compatibilité avec le frontend)"""
        return self.titre

