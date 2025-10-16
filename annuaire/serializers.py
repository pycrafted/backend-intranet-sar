from rest_framework import serializers
from django.db.models import Count
from django.contrib.auth import get_user_model
import re
from .models import Department, Employee

User = get_user_model()


class UserAnnuaireSerializer(serializers.ModelSerializer):
    """Sérialiseur optimisé pour l'annuaire utilisant les données de l'app authentication"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department', read_only=True)
    position_title = serializers.CharField(source='position', read_only=True)
    employee_id = serializers.CharField(read_only=True)
    matricule = serializers.CharField(source='employee_id', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 
            'phone_number', 'employee_id', 'position', 'position_title', 
            'department', 'department_name', 'matricule', 'is_active', 
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
    


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'employee_count', 'created_at', 'updated_at']
    
    def get_employee_count(self, obj):
        return obj.employees.count()


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des employés (version allégée)"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField()
    matricule = serializers.CharField(source='employee_id', read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone_fixed', 'phone_mobile',
            'employee_id', 'matricule', 'department', 'position_title', 'department_name',
            'avatar'
        ]
    
    def get_avatar(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                print(f"[AVATAR_URL] URL générée: {url}")
                return url
            # Fallback si pas de request (ex: tests)
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
            url = f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
            print(f"[AVATAR_URL] URL fallback: {url}")
            return url
        print(f"[AVATAR_URL] Aucun avatar pour {obj.full_name}")
        return None
    
    def validate_phone_fixed(self, value):
        """Valider l'unicité du numéro de téléphone fixe"""
        if value:
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone_fixed=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone fixe existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone_fixed=value).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone fixe existe déjà.')
            
            return value
        return value
    
    def validate_phone_mobile(self, value):
        """Valider l'unicité du numéro de téléphone mobile"""
        if value:
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone_mobile=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone mobile existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone_mobile=value).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone mobile existe déjà.')
            
            return value
        return value
    


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un employé"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField()
    matricule = serializers.CharField(source='employee_id', read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone_fixed', 'phone_mobile',
            'employee_id', 'matricule', 'department', 'position_title', 'department_name',
            'avatar',
            'created_at', 'updated_at'
        ]
    
    def get_avatar(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                print(f"[AVATAR_URL] URL générée: {url}")
                return url
            # Fallback si pas de request (ex: tests)
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
            url = f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
            print(f"[AVATAR_URL] URL fallback: {url}")
            return url
        print(f"[AVATAR_URL] Aucun avatar pour {obj.full_name}")
        return None
    
    def validate_phone_fixed(self, value):
        """Valider l'unicité du numéro de téléphone fixe"""
        if value:
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone_fixed=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone fixe existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone_fixed=value).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone fixe existe déjà.')
            
            return value
        return value
    
    def validate_phone_mobile(self, value):
        """Valider l'unicité du numéro de téléphone mobile"""
        if value:
            # Vérifier l'unicité
            if self.instance:
                # Mode édition
                if Employee.objects.filter(phone_mobile=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone mobile existe déjà.')
            else:
                # Mode création
                if Employee.objects.filter(phone_mobile=value).exists():
                    raise serializers.ValidationError('Un employé avec ce numéro de téléphone mobile existe déjà.')
            
            return value
        return value
    
    


class EmployeeHierarchySerializer(serializers.ModelSerializer):
    """Serializer pour l'organigramme hiérarchique"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone_fixed', 'phone_mobile',
            'employee_id', 'department', 'position_title', 'department_name',
            'avatar'
        ]


class DepartmentHierarchySerializer(serializers.ModelSerializer):
    """Serializer pour l'organigramme par département"""
    employees = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'employees']
    
    def get_employees(self, obj):
        """Retourne les employés du département"""
        employees = Employee.objects.filter(
            department=obj,
            is_active=True
        ).select_related('department')
        return EmployeeListSerializer(employees, many=True).data
