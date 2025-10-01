from django.db import models
from django.utils import timezone
from datetime import datetime, date, timedelta


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
    
    DEPARTMENT_CHOICES = [
        ('production', 'Production'),
        ('maintenance', 'Maintenance'),
        ('quality', 'Qualité'),
        ('safety', 'Sécurité'),
        ('logistics', 'Logistique'),
        ('it', 'Informatique'),
        ('hr', 'Ressources Humaines'),
        ('finance', 'Finance'),
        ('marketing', 'Marketing'),
        ('other', 'Autre'),
    ]
    
    # Champs principaux
    description = models.TextField(
        help_text="Description détaillée de l'idée"
    )
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
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
        return f"Idée #{self.id} - {self.get_department_display()} - {self.get_status_display()}"


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


class Questionnaire(models.Model):
    """
    Modèle pour gérer les questionnaires et sondages
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('closed', 'Fermé'),
        ('archived', 'Archivé'),
    ]
    
    TYPE_CHOICES = [
        ('survey', 'Sondage'),
        ('quiz', 'Quiz'),
        ('evaluation', 'Évaluation'),
        ('feedback', 'Retour d\'expérience'),
        ('poll', 'Sondage rapide'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('all', 'Tous les employés'),
        ('department', 'Département spécifique'),
        ('role', 'Rôle spécifique'),
        ('custom', 'Audience personnalisée'),
    ]
    
    # Informations de base
    title = models.CharField(
        max_length=200,
        verbose_name="Titre",
        help_text="Titre du questionnaire"
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Description détaillée du questionnaire",
        blank=True
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='survey',
        verbose_name="Type",
        help_text="Type de questionnaire"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Statut",
        help_text="Statut actuel du questionnaire"
    )
    
    # Configuration
    is_anonymous = models.BooleanField(
        default=True,
        verbose_name="Anonyme",
        help_text="Les réponses sont-elles anonymes ?"
    )
    allow_multiple_responses = models.BooleanField(
        default=False,
        verbose_name="Réponses multiples",
        help_text="Permettre plusieurs réponses par utilisateur"
    )
    show_results_after_submission = models.BooleanField(
        default=True,
        verbose_name="Afficher les résultats",
        help_text="Afficher les résultats après soumission"
    )
    
    # Ciblage
    target_audience_type = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='all',
        verbose_name="Type d'audience",
        help_text="Type d'audience ciblée"
    )
    target_departments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Départements ciblés",
        help_text="Liste des départements ciblés (si applicable)"
    )
    target_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Rôles ciblés",
        help_text="Liste des rôles ciblés (si applicable)"
    )
    
    # Dates
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début",
        help_text="Date et heure de début du questionnaire"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin",
        help_text="Date et heure de fin du questionnaire"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le questionnaire"
    )
    
    class Meta:
        verbose_name = "Questionnaire"
        verbose_name_plural = "Questionnaires"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"
    
    @property
    def is_active(self):
        """Vérifie si le questionnaire est actif"""
        if self.status != 'active':
            return False
        
        now = timezone.now()
        
        # Vérifier la date de début
        if self.start_date and now < self.start_date:
            return False
        
        # Vérifier la date de fin
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    @property
    def total_responses(self):
        """Nombre total de réponses"""
        return self.responses.count()
    
    @property
    def response_rate(self):
        """Taux de réponse (si audience connue)"""
        # Cette propriété sera calculée en fonction de l'audience ciblée
        return 0  # À implémenter selon les besoins


class Question(models.Model):
    """
    Modèle pour les questions d'un questionnaire
    """
    TYPE_CHOICES = [
        ('text', 'Texte libre'),
        ('single_choice', 'Choix unique'),
        ('multiple_choice', 'Choix multiple'),
        ('scale', 'Échelle'),
        ('date', 'Date'),
        ('file', 'Fichier'),
        ('rating', 'Note'),
        # Phase 1 - Nouveaux types
        ('rating_stars', 'Étoiles'),
        ('rating_numeric', 'Note sur 10'),
        ('satisfaction_scale', 'Échelle de satisfaction'),
        ('email', 'Email'),
        ('phone', 'Téléphone'),
        ('required_checkbox', 'Case obligatoire'),
        ('date_range', 'Plage de dates'),
        # Phase 2 - Fonctionnalités avancées
        ('ranking', 'Classement'),
        ('top_selection', 'Top 3'),
        ('matrix', 'Matrice de choix'),
        ('likert', 'Échelle de Likert'),
    ]
    
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Questionnaire"
    )
    text = models.TextField(
        verbose_name="Texte de la question",
        help_text="Question posée"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='single_choice',
        verbose_name="Type",
        help_text="Type de question"
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name="Obligatoire",
        help_text="La question est-elle obligatoire ?"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre",
        help_text="Ordre d'affichage de la question"
    )
    
    # Configuration spécifique au type
    options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Options",
        help_text="Options de réponse (pour choix multiple/unique)"
    )
    scale_min = models.IntegerField(
        default=1,
        verbose_name="Échelle minimum",
        help_text="Valeur minimum de l'échelle"
    )
    scale_max = models.IntegerField(
        default=5,
        verbose_name="Échelle maximum",
        help_text="Valeur maximum de l'échelle"
    )
    scale_labels = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Labels d'échelle",
        help_text="Labels pour les valeurs d'échelle"
    )
    
    # Phase 1 - Nouvelles propriétés pour les nouveaux types
    rating_max = models.IntegerField(
        default=5,
        verbose_name="Note maximum",
        help_text="Note maximum pour les étoiles et notes numériques"
    )
    rating_labels = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Labels de notation",
        help_text="Labels personnalisés pour les étoiles et notes"
    )
    satisfaction_options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Options de satisfaction",
        help_text="Options pour l'échelle de satisfaction"
    )
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Règles de validation",
        help_text="Règles de validation spécifiques (email, téléphone, etc.)"
    )
    checkbox_text = models.TextField(
        default="J'accepte les conditions",
        blank=True,
        verbose_name="Texte de la case",
        help_text="Texte affiché à côté de la case obligatoire"
    )
    
    # Phase 2 - Nouvelles propriétés pour les types avancés
    ranking_items = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Éléments à classer",
        help_text="Liste des éléments à classer par ordre de priorité"
    )
    top_selection_limit = models.IntegerField(
        default=3,
        verbose_name="Limite de sélection",
        help_text="Nombre maximum d'éléments à sélectionner"
    )
    matrix_questions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Questions de la matrice",
        help_text="Liste des questions pour la matrice"
    )
    matrix_options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Options de la matrice",
        help_text="Liste des options communes pour toutes les questions"
    )
    likert_scale = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Échelle de Likert",
        help_text="Options de l'échelle de Likert"
    )
    
    # Conditions
    depends_on_question = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Dépend de",
        help_text="Question dont dépend cette question"
    )
    show_condition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Condition d'affichage",
        help_text="Condition pour afficher cette question"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['questionnaire', 'order', 'created_at']
        unique_together = ['questionnaire', 'order']
    
    def __str__(self):
        return f"{self.questionnaire.title} - Q{self.order}: {self.text[:50]}..."


class QuestionnaireResponse(models.Model):
    """
    Modèle pour les réponses aux questionnaires
    """
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Questionnaire"
    )
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur",
        help_text="Utilisateur qui a répondu (null si anonyme)"
    )
    session_key = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Clé de session",
        help_text="Clé de session pour les réponses anonymes"
    )
    
    # Métadonnées
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Navigateur utilisé"
    )
    
    class Meta:
        verbose_name = "Réponse au questionnaire"
        verbose_name_plural = "Réponses aux questionnaires"
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['questionnaire']),
            models.Index(fields=['user']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else "Anonyme"
        return f"{self.questionnaire.title} - {user_info} ({self.submitted_at.strftime('%d/%m/%Y %H:%M')})"


class QuestionResponse(models.Model):
    """
    Modèle pour les réponses individuelles aux questions
    """
    response = models.ForeignKey(
        QuestionnaireResponse,
        on_delete=models.CASCADE,
        related_name='question_responses',
        verbose_name="Réponse"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_responses',
        verbose_name="Question"
    )
    
    # Réponse (stockée en JSON pour flexibilité)
    answer_data = models.JSONField(
        verbose_name="Données de réponse",
        help_text="Réponse stockée en format JSON"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Réponse à la question"
        verbose_name_plural = "Réponses aux questions"
        ordering = ['response', 'question__order']
        unique_together = ['response', 'question']
    
    def __str__(self):
        return f"{self.response} - {self.question.text[:30]}..."