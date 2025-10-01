from rest_framework import serializers
from django.db.models import Count
from django.contrib.auth import get_user_model
import re
from .models import Department, Position, Employee, OrganizationalChart

User = get_user_model()


class UserAnnuaireSerializer(serializers.ModelSerializer):
    """Sérialiseur optimisé pour l'annuaire utilisant les données de l'app authentication"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    manager_position = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department', read_only=True)
    position_title = serializers.CharField(source='position', read_only=True)
    employee_id = serializers.CharField(source='matricule', read_only=True)
    hierarchy_level = serializers.SerializerMethodField()
    is_manager = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 
            'phone_number', 'employee_id', 'position', 'position_title', 
            'department', 'department_name', 'matricule', 'manager', 'manager_name', 
            'manager_position', 'hierarchy_level', 'is_manager', 'is_active', 
            'is_staff', 'is_superuser', 'avatar', 'avatar_url', 'created_at', 'updated_at'
        ]
    
    def get_initials(self, obj):
        """Génère les initiales de l'utilisateur"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name[0]}{obj.last_name[0]}".upper()
        return "U"
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_manager_name(self, obj):
        """Retourne le nom du manager"""
        if obj.manager:
            return obj.manager.get_full_name()
        return None
    
    def get_manager_position(self, obj):
        """Retourne le poste du manager"""
        if obj.manager:
            return obj.manager.position
        return None
    
    def get_hierarchy_level(self, obj):
        """Détermine le niveau hiérarchique basé sur les permissions"""
        if obj.is_superuser:
            return 1
        elif obj.is_staff:
            return 2
        else:
            return 3
    
    def get_is_manager(self, obj):
        """Vérifie si l'utilisateur est un manager"""
        return obj.is_staff or obj.is_superuser


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'location', 'employee_count', 'created_at', 'updated_at']
    
    def get_employee_count(self, obj):
        return obj.positions.aggregate(
            total=Count('employees')
        )['total'] or 0


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = ['id', 'title', 'department', 'department_name', 'level', 'description', 'is_management', 'employee_count']
    
    def get_employee_count(self, obj):
        return obj.employees.count()


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des employés (version allégée)"""
    department_name = serializers.CharField(source='position.department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    hierarchy_level = serializers.ReadOnlyField()
    is_manager = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone',
            'employee_id', 'position', 'position_title', 'department_name', 'manager',
            'manager_name', 'hierarchy_level', 'is_manager', 'office_location',
            'work_schedule', 'is_active', 'hire_date', 'avatar'
        ]
    
    def validate_phone(self, value):
        """Valider et normaliser le numéro de téléphone"""
        if value:
            # Normaliser le numéro
            normalized_phone = self.normalize_phone(value)
            
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone=normalized_phone).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone=normalized_phone).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone existe déjà.')
            
            return normalized_phone
        return value
    
    def normalize_phone(self, phone):
        """Normaliser un numéro de téléphone"""
        if not phone:
            return phone
        
        # Supprimer tous les caractères non numériques sauf +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Ajouter +221 si le numéro commence par 77, 78, 76, 70
        if normalized.startswith(('77', '78', '76', '70')) and not normalized.startswith('+'):
            normalized = '+221' + normalized
        
        return normalized


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un employé"""
    department_name = serializers.CharField(source='position.department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    hierarchy_level = serializers.ReadOnlyField()
    is_manager = serializers.ReadOnlyField()
    subordinates = EmployeeListSerializer(many=True, read_only=True)
    management_chain = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone',
            'employee_id', 'position', 'position_title', 'department_name', 'manager',
            'manager_name', 'hierarchy_level', 'is_manager', 'office_location',
            'work_schedule', 'is_active', 'hire_date', 'avatar', 'subordinates',
            'management_chain', 'created_at', 'updated_at'
        ]
    
    def validate_phone(self, value):
        """Valider et normaliser le numéro de téléphone"""
        if value:
            # Normaliser le numéro
            normalized_phone = self.normalize_phone(value)
            
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone=normalized_phone).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone=normalized_phone).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone existe déjà.')
            
            return normalized_phone
        return value
    
    def normalize_phone(self, phone):
        """Normaliser un numéro de téléphone"""
        if not phone:
            return phone
        
        # Supprimer tous les caractères non numériques sauf +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Ajouter +221 si le numéro commence par 77, 78, 76, 70
        if normalized.startswith(('77', '78', '76', '70')) and not normalized.startswith('+'):
            normalized = '+221' + normalized
        
        return normalized
    
    def get_management_chain(self, obj):
        """Retourne la chaîne de management"""
        chain = obj.get_management_chain()
        return EmployeeListSerializer(chain, many=True).data


class OrganizationalChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationalChart
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class EmployeeHierarchySerializer(serializers.ModelSerializer):
    """Serializer pour l'organigramme hiérarchique"""
    children = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='position.department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    hierarchy_level = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone',
            'employee_id', 'position', 'position_title', 'department_name', 'hierarchy_level',
            'office_location', 'avatar', 'children'
        ]
    
    def get_children(self, obj):
        """Retourne les subordonnés directs"""
        subordinates = obj.subordinates.filter(is_active=True)
        return EmployeeHierarchySerializer(subordinates, many=True).data


class DepartmentHierarchySerializer(serializers.ModelSerializer):
    """Serializer pour l'organigramme par département"""
    employees = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'location', 'manager', 'employees']
    
    def get_employees(self, obj):
        """Retourne les employés du département"""
        employees = Employee.objects.filter(
            position__department=obj,
            is_active=True
        ).select_related('position', 'manager')
        return EmployeeListSerializer(employees, many=True).data
    
    def get_manager(self, obj):
        """Retourne le manager du département"""
        manager = Employee.objects.filter(
            position__department=obj,
            position__is_management=True,
            is_active=True
        ).first()
        if manager:
            return EmployeeListSerializer(manager).data
        return None
