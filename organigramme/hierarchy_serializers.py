from rest_framework import serializers
from .models import Agent


class AgentHierarchySerializer(serializers.ModelSerializer):
    """Serializer spécialisé pour les informations de hiérarchie"""
    
    hierarchy_info = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    subordinates_count = serializers.SerializerMethodField()
    all_subordinates_count = serializers.SerializerMethodField()
    hierarchy_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'job_title',
            'hierarchy_level',
            'is_manager',
            'manager',
            'manager_name',
            'subordinates_count',
            'all_subordinates_count',
            'hierarchy_path',
            'hierarchy_info'
        ]
    
    def get_hierarchy_info(self, obj):
        """Retourne les informations complètes de hiérarchie"""
        return obj.get_hierarchy_info()
    
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.full_name
        return None
    
    def get_subordinates_count(self, obj):
        """Retourne le nombre de subordonnés directs"""
        return obj.subordinates.count()
    
    def get_all_subordinates_count(self, obj):
        """Retourne le nombre total de subordonnés (directs et indirects)"""
        return len(obj.get_all_subordinates())
    
    def get_hierarchy_path(self, obj):
        """Retourne le chemin hiérarchique complet"""
        return [agent.full_name for agent in obj.get_hierarchy_path()]
