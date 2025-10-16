from rest_framework import serializers
from .models import Direction, Agent
from django.conf import settings


class DirectionSerializer(serializers.ModelSerializer):
    """Serializer pour les directions"""
    
    class Meta:
        model = Direction
        fields = ['id', 'name']


class AgentSerializer(serializers.ModelSerializer):
    """Serializer pour les agents avec toutes les informations"""
    
    directions = DirectionSerializer(many=True, read_only=True)
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'initials',
            'job_title',
            'directions',
            'email',
            'phone_fixed',
            'phone_mobile',
            'matricule',
            'position',
            'department_name',
            'hierarchy_level',
            'is_manager',
            'is_active',
            'avatar',
            'office_location',
            'manager',
            'manager_name',
            'created_at',
            'updated_at'
        ]
    
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.full_name
        return None
    
    def get_department_name(self, obj):
        """Retourne le nom du département principal"""
        if obj.department_name:
            return obj.department_name
        elif obj.directions.exists():
            return obj.directions.first().name
        return None
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            data['avatar'] = f"http://localhost:8000{settings.MEDIA_URL}{instance.avatar}"
        else:
            # Avatar par défaut si aucun avatar n'est uploadé
            data['avatar'] = None
        return data


class AgentListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des agents"""
    
    directions = DirectionSerializer(many=True, read_only=True)
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'initials',
            'job_title',
            'directions',
            'email',
            'phone_fixed',
            'phone_mobile',
            'matricule',
            'position',
            'department_name',
            'hierarchy_level',
            'is_manager',
            'is_active',
            'avatar',
            'office_location',
            'manager',
            'manager_name'
        ]
    
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.full_name
        return None
    
    def get_department_name(self, obj):
        """Retourne le nom du département principal"""
        if obj.department_name:
            return obj.department_name
        elif obj.directions.exists():
            return obj.directions.first().name
        return None
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            data['avatar'] = f"http://localhost:8000{settings.MEDIA_URL}{instance.avatar}"
        else:
            # Avatar par défaut si aucun avatar n'est uploadé
            data['avatar'] = None
        return data


class AgentTreeSerializer(serializers.ModelSerializer):
    """Serializer pour l'arborescence hiérarchique"""
    
    subordinates = serializers.SerializerMethodField()
    directions = DirectionSerializer(many=True, read_only=True)
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'initials',
            'job_title',
            'directions',
            'email',
            'phone_fixed',
            'phone_mobile',
            'matricule',
            'position',
            'department_name',
            'hierarchy_level',
            'is_manager',
            'is_active',
            'avatar',
            'office_location',
            'manager',
            'manager_name',
            'subordinates'
        ]
    
    def get_subordinates(self, obj):
        """Retourne les subordonnés de l'agent"""
        subordinates = obj.subordinates.all()
        return AgentTreeSerializer(subordinates, many=True, context=self.context).data
    
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.full_name
        return None
    
    def get_department_name(self, obj):
        """Retourne le nom du département principal"""
        if obj.department_name:
            return obj.department_name
        elif obj.directions.exists():
            return obj.directions.first().name
        return None
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            data['avatar'] = f"http://localhost:8000{settings.MEDIA_URL}{instance.avatar}"
        else:
            # Avatar par défaut si aucun avatar n'est uploadé
            data['avatar'] = None
        return data