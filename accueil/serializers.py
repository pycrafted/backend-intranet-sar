from rest_framework import serializers
from django.utils import timezone
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Questionnaire, Question, QuestionnaireResponse, QuestionResponse


class SafetyDataSerializer(serializers.ModelSerializer):
    """
    Serializer pour les données de sécurité du travail
    """
    appreciation_sar = serializers.ReadOnlyField()
    appreciation_ee = serializers.ReadOnlyField()
    
    # Champs pour compatibilité avec le frontend
    daysWithoutIncidentSAR = serializers.SerializerMethodField()
    daysWithoutIncidentEE = serializers.SerializerMethodField()
    lastIncidentDateSAR = serializers.SerializerMethodField()
    lastIncidentDateEE = serializers.SerializerMethodField()
    lastIncidentTypeSAR = serializers.SerializerMethodField()
    lastIncidentTypeEE = serializers.SerializerMethodField()
    lastIncidentDescriptionSAR = serializers.SerializerMethodField()
    lastIncidentDescriptionEE = serializers.SerializerMethodField()
    safetyScore = serializers.SerializerMethodField()
    
    class Meta:
        model = SafetyData
        fields = [
            'id',
            'days_without_incident_sar',
            'days_without_incident_ee',
            'appreciation_sar',
            'appreciation_ee',
            'created_at',
            'updated_at',
            # Champs pour compatibilité frontend
            'daysWithoutIncidentSAR',
            'daysWithoutIncidentEE',
            'lastIncidentDateSAR',
            'lastIncidentDateEE',
            'lastIncidentTypeSAR',
            'lastIncidentTypeEE',
            'lastIncidentDescriptionSAR',
            'lastIncidentDescriptionEE',
            'safetyScore',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_daysWithoutIncidentSAR(self, obj):
        return obj.days_without_incident_sar
    
    def get_daysWithoutIncidentEE(self, obj):
        return obj.days_without_incident_ee
    
    def get_lastIncidentDateSAR(self, obj):
        return obj.last_incident_date_sar.isoformat() if obj.last_incident_date_sar else None
    
    def get_lastIncidentDateEE(self, obj):
        return obj.last_incident_date_ee.isoformat() if obj.last_incident_date_ee else None
    
    def get_lastIncidentTypeSAR(self, obj):
        return obj.last_incident_type_sar
    
    def get_lastIncidentTypeEE(self, obj):
        return obj.last_incident_type_ee
    
    def get_lastIncidentDescriptionSAR(self, obj):
        return obj.last_incident_description_sar
    
    def get_lastIncidentDescriptionEE(self, obj):
        return obj.last_incident_description_ee
    
    def get_safetyScore(self, obj):
        # Mettre à jour le score avant de le retourner
        obj.update_safety_score()
        return obj.safety_score


class SafetyDataCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour des données de sécurité
    """
    class Meta:
        model = SafetyData
        fields = [
            'last_incident_date_sar',
            'last_incident_date_ee',
            'last_incident_type_sar',
            'last_incident_type_ee',
            'last_incident_description_sar',
            'last_incident_description_ee',
            'safety_score'
        ]
    
    def validate(self, data):
        # Validation des champs de sécurité
        safety_score = data.get('safety_score', 0)
        
        if safety_score < 0 or safety_score > 100:
            raise serializers.ValidationError("Le score de sécurité doit être entre 0 et 100.")
        
        return data


class IdeaSerializer(serializers.ModelSerializer):
    """
    Serializer pour les idées soumises
    """
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Idea
        fields = [
            'id',
            'description',
            'department',
            'department_display',
            'status',
            'status_display',
            'submitted_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'updated_at']


class IdeaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'idées
    """
    class Meta:
        model = Idea
        fields = ['description', 'department']
    
    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La description de l'idée est obligatoire.")
        
        if len(value.strip()) < 5:
            raise serializers.ValidationError("La description doit contenir au moins 5 caractères.")
        
        return value.strip()
    
    def validate_department(self, value):
        valid_departments = [choice[0] for choice in Idea.DEPARTMENT_CHOICES]
        if value not in valid_departments:
            raise serializers.ValidationError("Département invalide.")
        
        return value


class IdeaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour des idées (statut)
    """
    class Meta:
        model = Idea
        fields = ['status']
    
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Idea.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Statut invalide.")
        
        return value


# ===== SERIALIZERS POUR LE MENU =====

class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer pour les plats du menu
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'type',
            'type_display',
            'description',
            'is_available',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MenuItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour des plats
    """
    class Meta:
        model = MenuItem
        fields = ['name', 'type', 'description', 'is_available']
    
    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du plat est obligatoire.")
        return value.strip()
    
    def validate_type(self, value):
        valid_types = [choice[0] for choice in MenuItem.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Type de cuisine invalide.")
        return value


class DayMenuSerializer(serializers.ModelSerializer):
    """
    Serializer pour les menus des jours
    """
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    senegalese = MenuItemSerializer(read_only=True)
    european = MenuItemSerializer(read_only=True)
    senegalese_id = serializers.IntegerField(write_only=True)
    european_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DayMenu
        fields = [
            'id',
            'day',
            'day_display',
            'date',
            'senegalese',
            'european',
            'senegalese_id',
            'european_id',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date(self, value):
        # Permettre la création de menus pour TOUS les jours de la semaine courante
        # Inclure les jours passés, présents et futurs
        return value
    
    def validate_senegalese_id(self, value):
        try:
            menu_item = MenuItem.objects.get(id=value, type='senegalese')
            if not menu_item.is_available:
                raise serializers.ValidationError("Ce plat sénégalais n'est pas disponible.")
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Plat sénégalais invalide.")
        return value
    
    def validate_european_id(self, value):
        try:
            menu_item = MenuItem.objects.get(id=value, type='european')
            if not menu_item.is_available:
                raise serializers.ValidationError("Ce plat européen n'est pas disponible.")
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Plat européen invalide.")
        return value
    
    def create(self, validated_data):
        senegalese_id = validated_data.pop('senegalese_id')
        european_id = validated_data.pop('european_id')
        
        validated_data['senegalese'] = MenuItem.objects.get(id=senegalese_id)
        validated_data['european'] = MenuItem.objects.get(id=european_id)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'senegalese_id' in validated_data:
            senegalese_id = validated_data.pop('senegalese_id')
            instance.senegalese = MenuItem.objects.get(id=senegalese_id)
        
        if 'european_id' in validated_data:
            european_id = validated_data.pop('european_id')
            instance.european = MenuItem.objects.get(id=european_id)
        
        return super().update(instance, validated_data)


class DayMenuCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la création et la mise à jour des menus
    """
    class Meta:
        model = DayMenu
        fields = ['day', 'date', 'senegalese', 'european', 'is_active']
    
    def validate_date(self, value):
        # Permettre la création de menus pour TOUS les jours de la semaine courante
        # Inclure les jours passés, présents et futurs
        return value


class WeekMenuSerializer(serializers.Serializer):
    """
    Serializer pour le menu de la semaine complet
    """
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    days = DayMenuSerializer(many=True)
    
    def to_representation(self, instance):
        # Logique pour formater le menu de la semaine
        return super().to_representation(instance)


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer pour les événements - Lecture seule
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_past = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    is_future = serializers.ReadOnlyField()
    
    # Champs formatés pour le frontend
    time_formatted = serializers.SerializerMethodField()
    date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'time', 'location', 
            'type', 'type_display', 'attendees', 'is_all_day',
            'created_at', 'updated_at', 'is_past', 'is_today', 'is_future',
            'time_formatted', 'date_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_formatted(self, obj):
        """Formate l'heure pour le frontend (HH:MM)"""
        if obj.time:
            return obj.time.strftime('%H:%M')
        return None
    
    def get_date_formatted(self, obj):
        """Formate la date pour le frontend (ISO format)"""
        return obj.date.isoformat()


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et modification des événements
    """
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'date', 'time', 'location', 
            'type', 'attendees', 'is_all_day'
        ]
    
    def validate_date(self, value):
        """Validation de la date"""
        # Pour la modification, on permet de garder une date dans le passé
        # Seulement pour la création, on bloque les dates passées
        if not self.instance and value < timezone.now().date():
            raise serializers.ValidationError("La date ne peut pas être dans le passé.")
        return value
    
    def validate_time(self, value):
        """Validation de l'heure"""
        if value and not self.initial_data.get('is_all_day', False):
            # Si ce n'est pas un événement toute la journée, l'heure est requise
            return value
        elif self.initial_data.get('is_all_day', False):
            # Si c'est un événement toute la journée, l'heure n'est pas nécessaire
            return None
        return value
    
    def validate(self, data):
        """Validation globale"""
        # Si c'est un événement toute la journée, on ignore l'heure
        if data.get('is_all_day', False):
            data['time'] = None
        
        return data


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les listes d'événements
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'date', 'time_formatted', 'location', 
            'type', 'type_display', 'attendees', 'is_all_day'
        ]
    
    def get_time_formatted(self, obj):
        """Formate l'heure pour le frontend (HH:MM)"""
        if obj.time:
            return obj.time.strftime('%H:%M')
        return None


# ===== SERIALIZERS POUR LES QUESTIONNAIRES =====

class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les questions d'un questionnaire
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'type', 'type_display', 'is_required', 'order',
            'options', 'scale_min', 'scale_max', 'scale_labels',
            'depends_on_question', 'show_condition', 'created_at', 'updated_at',
            # Phase 1 - Nouveaux champs
            'rating_max', 'rating_labels', 'satisfaction_options', 
            'validation_rules', 'checkbox_text',
            # Phase 2 - Nouveaux champs
            'ranking_items', 'top_selection_limit', 'matrix_questions',
            'matrix_options', 'likert_scale'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et modification des questions
    """
    class Meta:
        model = Question
        fields = [
            'text', 'type', 'is_required', 'order', 'options',
            'scale_min', 'scale_max', 'scale_labels',
            'depends_on_question', 'show_condition',
            # Phase 1 - Nouveaux champs
            'rating_max', 'rating_labels', 'satisfaction_options', 
            'validation_rules', 'checkbox_text',
            # Phase 2 - Nouveaux champs
            'ranking_items', 'top_selection_limit', 'matrix_questions',
            'matrix_options', 'likert_scale'
        ]
    
    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le texte de la question est obligatoire.")
        return value.strip()
    
    def validate_type(self, value):
        valid_types = [choice[0] for choice in Question.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Type de question invalide.")
        return value
    
    def validate_scale_min(self, value):
        if value < 0:
            raise serializers.ValidationError("La valeur minimum de l'échelle ne peut pas être négative.")
        return value
    
    def validate_scale_max(self, value):
        if value < 1:
            raise serializers.ValidationError("La valeur maximum de l'échelle doit être au moins 1.")
        return value
    
    def validate_rating_max(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("La note maximum doit être entre 1 et 10.")
        return value
    
    def validate_top_selection_limit(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("La limite de sélection doit être entre 1 et 10.")
        return value
    
    def validate(self, data):
        # Validation des échelles
        if data.get('type') == 'scale':
            scale_min = data.get('scale_min', 1)
            scale_max = data.get('scale_max', 5)
            if scale_min >= scale_max:
                raise serializers.ValidationError("La valeur minimum doit être inférieure à la valeur maximum.")
        
        # Validation des options pour les questions à choix
        if data.get('type') in ['single_choice', 'multiple_choice']:
            options = data.get('options', [])
            if not options or len(options) < 2:
                raise serializers.ValidationError("Les questions à choix doivent avoir au moins 2 options.")
        
        return data


class QuestionnaireSerializer(serializers.ModelSerializer):
    """
    Serializer pour les questionnaires - Lecture seule
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_audience_type_display = serializers.CharField(source='get_target_audience_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    total_responses = serializers.ReadOnlyField()
    response_rate = serializers.ReadOnlyField()
    questions = QuestionSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Questionnaire
        fields = [
            'id', 'title', 'description', 'type', 'type_display', 'status', 'status_display',
            'is_anonymous', 'allow_multiple_responses', 'show_results_after_submission',
            'target_audience_type', 'target_audience_type_display', 'target_departments', 'target_roles',
            'start_date', 'end_date', 'created_at', 'updated_at', 'created_by', 'created_by_name',
            'is_active', 'total_responses', 'response_rate', 'questions'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return "Utilisateur inconnu"


class QuestionnaireCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et modification des questionnaires
    """
    questions = QuestionCreateUpdateSerializer(many=True, required=False)
    
    class Meta:
        model = Questionnaire
        fields = [
            'id', 'title', 'description', 'type', 'status', 'is_anonymous',
            'allow_multiple_responses', 'show_results_after_submission',
            'target_audience_type', 'target_departments', 'target_roles',
            'start_date', 'end_date', 'questions'
        ]
        read_only_fields = ['id']
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le titre du questionnaire est obligatoire.")
        return value.strip()
    
    def validate_type(self, value):
        valid_types = [choice[0] for choice in Questionnaire.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Type de questionnaire invalide.")
        return value
    
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Questionnaire.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Statut invalide.")
        return value
    
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        questionnaire = Questionnaire.objects.create(**validated_data)
        
        # Créer les questions associées
        for question_data in questions_data:
            Question.objects.create(questionnaire=questionnaire, **question_data)
        
        return questionnaire
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        # Mettre à jour le questionnaire
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les questions
        if questions_data:
            # Supprimer les anciennes questions
            instance.questions.all().delete()
            
            # Créer les nouvelles questions
            for question_data in questions_data:
                Question.objects.create(questionnaire=instance, **question_data)
        
        return instance
    
    def validate_target_audience_type(self, value):
        valid_types = [choice[0] for choice in Questionnaire.TARGET_AUDIENCE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Type d'audience invalide.")
        return value
    
    def validate(self, data):
        # Validation des dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("La date de début doit être antérieure à la date de fin.")
        
        # Validation du ciblage
        target_audience_type = data.get('target_audience_type', 'all')
        target_departments = data.get('target_departments', [])
        target_roles = data.get('target_roles', [])
        
        if target_audience_type == 'department' and not target_departments:
            raise serializers.ValidationError("Les départements ciblés sont requis pour ce type d'audience.")
        
        if target_audience_type == 'role' and not target_roles:
            raise serializers.ValidationError("Les rôles ciblés sont requis pour ce type d'audience.")
        
        return data


class QuestionnaireListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les listes de questionnaires
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    total_responses = serializers.ReadOnlyField()
    response_rate = serializers.ReadOnlyField()
    questions_count = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Questionnaire
        fields = [
            'id', 'title', 'description', 'type', 'type_display', 'status', 'status_display',
            'is_anonymous', 'allow_multiple_responses', 'show_results_after_submission',
            'target_audience_type', 'target_departments', 'target_roles',
            'start_date', 'end_date', 'created_at', 'updated_at', 'created_by_name', 
            'is_active', 'total_responses', 'response_rate', 'questions_count', 'questions'
        ]
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    
    def get_questions(self, obj):
        """Sérialiser les questions du questionnaire"""
        questions = obj.questions.all().order_by('order')
        return [
            {
                'id': q.id,
                'text': q.text,
                'type': q.type,
                'type_display': q.get_type_display(),
                'is_required': q.is_required,
                'order': q.order,
                'options': q.options,
                'scale_min': q.scale_min,
                'scale_max': q.scale_max,
                'scale_labels': q.scale_labels,
                'rating_max': q.rating_max,
                'rating_labels': q.rating_labels,
                'satisfaction_options': q.satisfaction_options,
                'validation_rules': q.validation_rules,
                'checkbox_text': q.checkbox_text,
                'ranking_items': q.ranking_items,
                'top_selection_limit': q.top_selection_limit,
                'matrix_questions': q.matrix_questions,
                'matrix_options': q.matrix_options,
                'likert_scale': q.likert_scale
            }
            for q in questions
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return "Utilisateur inconnu"


class QuestionResponseSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réponses aux questions
    """
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.type', read_only=True)
    
    class Meta:
        model = QuestionResponse
        fields = ['id', 'question', 'question_text', 'question_type', 'answer_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réponses aux questionnaires
    """
    user_name = serializers.SerializerMethodField()
    question_responses = QuestionResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionnaireResponse
        fields = [
            'id', 'questionnaire', 'user', 'user_name', 'session_key',
            'submitted_at', 'ip_address', 'user_agent', 'question_responses'
        ]
        read_only_fields = ['id', 'submitted_at']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Anonyme"


class QuestionnaireResponseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de réponses aux questionnaires
    """
    question_responses = QuestionResponseSerializer(many=True, write_only=True)
    
    class Meta:
        model = QuestionnaireResponse
        fields = ['questionnaire', 'session_key', 'ip_address', 'user_agent', 'question_responses']
    
    def validate_questionnaire(self, value):
        # Vérifier que le questionnaire est actif
        if not value.is_active:
            raise serializers.ValidationError("Ce questionnaire n'est pas actif.")
        
        # Vérifier les dates
        now = timezone.now()
        if value.start_date and now < value.start_date:
            raise serializers.ValidationError("Ce questionnaire n'est pas encore ouvert.")
        
        if value.end_date and now > value.end_date:
            raise serializers.ValidationError("Ce questionnaire est fermé.")
        
        return value
    
    def validate(self, data):
        questionnaire = data.get('questionnaire')
        question_responses = data.get('question_responses', [])
        
        # Vérifier que toutes les questions obligatoires sont répondues
        required_questions = questionnaire.questions.filter(is_required=True)
        answered_question_ids = [qr.get('question').id for qr in question_responses]
        
        for question in required_questions:
            if question.id not in answered_question_ids:
                raise serializers.ValidationError(f"La question '{question.text}' est obligatoire.")
        
        return data
    
    def create(self, validated_data):
        question_responses_data = validated_data.pop('question_responses')
        response = QuestionnaireResponse.objects.create(**validated_data)
        
        # Créer les réponses aux questions
        for qr_data in question_responses_data:
            QuestionResponse.objects.create(response=response, **qr_data)
        
        return response