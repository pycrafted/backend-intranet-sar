from rest_framework import serializers
from django.utils import timezone
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Department, Project


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


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les départements
    """
    class Meta:
        model = Department
        fields = [
            'id',
            'code',
            'name',
            'emails',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_emails(self, value):
        """
        Valide que les emails sont bien formatés
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Les emails doivent être une liste.")
        
        for email in value:
            if not isinstance(email, str) or '@' not in email:
                raise serializers.ValidationError(f"Email invalide: {email}")
        
        return value


class IdeaSerializer(serializers.ModelSerializer):
    """
    Serializer pour les idées soumises
    """
    department_display = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)
    
    class Meta:
        model = Idea
        fields = [
            'id',
            'description',
            'department',
            'department_display',
            'department_code',
            'department_detail',
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
        """
        Valide que le département existe et est actif
        """
        if not value:
            raise serializers.ValidationError("Le département est obligatoire.")
        
        if not value.is_active:
            raise serializers.ValidationError("Ce département n'est pas actif.")
        
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
    dessert = MenuItemSerializer(read_only=True, allow_null=True)
    senegalese_id = serializers.IntegerField(write_only=True)
    european_id = serializers.IntegerField(write_only=True)
    dessert_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = DayMenu
        fields = [
            'id',
            'day',
            'day_display',
            'date',
            'senegalese',
            'european',
            'dessert',
            'senegalese_id',
            'european_id',
            'dessert_id',
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
    
    def validate_dessert_id(self, value):
        if value is None:
            return None
        try:
            menu_item = MenuItem.objects.get(id=value, type='dessert')
            if not menu_item.is_available:
                raise serializers.ValidationError("Ce dessert n'est pas disponible.")
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Dessert invalide.")
        return value
    
    def create(self, validated_data):
        senegalese_id = validated_data.pop('senegalese_id')
        european_id = validated_data.pop('european_id')
        dessert_id = validated_data.pop('dessert_id', None)
        
        validated_data['senegalese'] = MenuItem.objects.get(id=senegalese_id)
        validated_data['european'] = MenuItem.objects.get(id=european_id)
        if dessert_id:
            validated_data['dessert'] = MenuItem.objects.get(id=dessert_id)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'senegalese_id' in validated_data:
            senegalese_id = validated_data.pop('senegalese_id')
            instance.senegalese = MenuItem.objects.get(id=senegalese_id)
        
        if 'european_id' in validated_data:
            european_id = validated_data.pop('european_id')
            instance.european = MenuItem.objects.get(id=european_id)
        
        if 'dessert_id' in validated_data:
            dessert_id = validated_data.pop('dessert_id')
            if dessert_id:
                instance.dessert = MenuItem.objects.get(id=dessert_id)
            else:
                instance.dessert = None
        
        return super().update(instance, validated_data)


class DayMenuCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la création et la mise à jour des menus
    """
    class Meta:
        model = DayMenu
        fields = ['day', 'date', 'senegalese', 'european', 'dessert', 'is_active']
    
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


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer pour les projets stratégiques
    Compatible avec le frontend (champs camelCase)
    """
    # Propriétés calculées
    duration_days = serializers.ReadOnlyField()
    duration_formatted = serializers.ReadOnlyField()
    
    # Champs pour compatibilité avec le frontend (camelCase)
    name = serializers.CharField(source='titre', read_only=False, required=False, allow_blank=True, allow_null=True)
    chefProjet = serializers.SerializerMethodField()
    dateDebut = serializers.SerializerMethodField()
    dateFin = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'titre',
            'name',  # Alias pour compatibilité frontend
            'objective',
            'description',
            'status',
            'date_debut',
            'date_fin',
            'partners',
            'chef_projet',
            'image',
            'created_at',
            'updated_at',
            # Propriétés calculées
            'duration_days',
            'duration_formatted',
            # Champs pour compatibilité frontend
            'chefProjet',
            'dateDebut',
            'dateFin',
            'image',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_days', 'duration_formatted']
    
    def get_chefProjet(self, obj):
        """Retourne le chef de projet pour compatibilité frontend"""
        return obj.chef_projet
    
    def get_dateDebut(self, obj):
        """Retourne la date de début formatée pour compatibilité frontend"""
        return obj.date_debut.isoformat() if obj.date_debut else None
    
    def get_dateFin(self, obj):
        """Retourne la date de fin formatée pour compatibilité frontend"""
        return obj.date_fin.isoformat() if obj.date_fin else None
    
    def get_image(self, obj):
        """Retourne l'URL de l'image uploadée"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def to_internal_value(self, data):
        """Convertit 'name' en 'titre' pour la compatibilité frontend"""
        if 'name' in data and 'titre' not in data:
            data = data.copy()
            data['titre'] = data.pop('name')
        return super().to_internal_value(data)


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour des projets
    Tous les champs sont optionnels
    """
    name = serializers.CharField(source='titre', required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Project
        fields = [
            'titre',
            'name',  # Alias pour compatibilité frontend
            'objective',
            'description',
            'status',
            'date_debut',
            'date_fin',
            'partners',
            'chef_projet',
            'image',
        ]
    
    def validate_status(self, value):
        """Valide le statut si fourni"""
        if value:
            valid_statuses = [choice[0] for choice in Project.STATUS_CHOICES]
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Statut invalide. Choix possibles: {', '.join(valid_statuses)}")
        return value
    
    def to_internal_value(self, data):
        """Convertit 'name' en 'titre' pour la compatibilité frontend"""
        if 'name' in data and 'titre' not in data:
            data = data.copy()
            data['titre'] = data.pop('name')
        return super().to_internal_value(data)
