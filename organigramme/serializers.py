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
    directions_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Direction.objects.all(), 
        source='directions',
        write_only=True,
        required=False
    )
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    main_direction_name = serializers.SerializerMethodField()
    
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
            'directions_ids',
            'email',
            'phone_fixed',
            'phone_mobile',
            'matricule',
            'main_direction',
            'main_direction_name',
            'hierarchy_level',
            'avatar',
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
    
    def get_main_direction_name(self, obj):
        """Retourne le nom de la direction principale"""
        if obj.main_direction:
            return obj.main_direction.name
        return "Non renseigné"
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            request = self.context.get('request')
            if request:
                data['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                # Fallback pour la production
                base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
                data['avatar'] = f"{base_url}{settings.MEDIA_URL}{instance.avatar.name}"
        else:
            # Avatar par défaut si aucun avatar n'est uploadé
            data['avatar'] = None
        return data


class AgentListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des agents"""
    
    directions = DirectionSerializer(many=True, read_only=True)
    directions_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Direction.objects.all(), 
        source='directions',
        write_only=True,
        required=False
    )
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    main_direction_name = serializers.SerializerMethodField()
    
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
            'directions_ids',
            'email',
            'phone_fixed',
            'phone_mobile',
            'matricule',
            'main_direction',
            'main_direction_name',
            'hierarchy_level',
            'avatar',
            'manager',
            'manager_name'
        ]
    
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.full_name
        return None
    
    def get_main_direction_name(self, obj):
        """Retourne le nom de la direction principale"""
        if obj.main_direction:
            return obj.main_direction.name
        return "Non renseigné"
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            request = self.context.get('request')
            if request:
                data['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                # Fallback pour la production
                base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
                data['avatar'] = f"{base_url}{settings.MEDIA_URL}{instance.avatar.name}"
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
    main_direction_name = serializers.SerializerMethodField()
    
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
            'main_direction_name',
            'hierarchy_level',
            'avatar',
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
    
    def get_main_direction_name(self, obj):
        """Retourne le nom de la direction principale"""
        if obj.main_direction:
            return obj.main_direction.name
        return "Non renseigné"
    
    def to_representation(self, instance):
        """Override pour formater l'URL de l'avatar"""
        data = super().to_representation(instance)
        if instance.avatar:
            # Construire l'URL complète de l'avatar
            request = self.context.get('request')
            if request:
                data['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                # Fallback pour la production
                base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
                data['avatar'] = f"{base_url}{settings.MEDIA_URL}{instance.avatar.name}"
        else:
            # Avatar par défaut si aucun avatar n'est uploadé
            data['avatar'] = None
        return data