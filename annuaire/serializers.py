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
    
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 
            'phone_number', 'position', 'position_title', 
            'department', 'department_name', 'is_active', 
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
    avatar = serializers.SerializerMethodField()  # Transformer en URL complète
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone_fixed', 'phone_mobile',
            'department', 'position_title', 'department_name',
            'avatar'
        ]
    
    def get_avatar(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            else:
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                return f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
        return None
    
    def create(self, validated_data):
        """Création d'un employé avec logs détaillés"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[EMPLOYEE_SERIALIZER] Données validées: {validated_data}")
        
        # Logs spécifiques pour l'avatar
        if 'avatar' in validated_data:
            avatar = validated_data['avatar']
            logger.info(f"[EMPLOYEE_SERIALIZER] Avatar dans validated_data:")
            logger.info(f"  - Nom: {avatar.name}")
            logger.info(f"  - Taille: {avatar.size} bytes")
            logger.info(f"  - Type: {avatar.content_type}")
        else:
            logger.info(f"[EMPLOYEE_SERIALIZER] Aucun avatar dans validated_data")
        
        try:
            # Créer l'employé
            employee = Employee.objects.create(**validated_data)
            logger.info(f"[EMPLOYEE_SERIALIZER] Employé créé avec succès: {employee.full_name} (ID: {employee.id})")
            
            # Vérifier l'avatar après création
            if employee.avatar:
                logger.info(f"[EMPLOYEE_SERIALIZER] Avatar sauvegardé après création:")
                logger.info(f"  - URL: {employee.avatar.url}")
                logger.info(f"  - Nom: {employee.avatar.name}")
                logger.info(f"  - Taille: {employee.avatar.size} bytes")
            else:
                logger.info(f"[EMPLOYEE_SERIALIZER] Aucun avatar sauvegardé après création")
            
            return employee
        except Exception as e:
            logger.error(f"[EMPLOYEE_SERIALIZER] Erreur lors de la création: {str(e)}")
            raise serializers.ValidationError(f"Erreur lors de la création de l'employé: {str(e)}")
    
    def validate(self, data):
        """Validation globale des données"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[EMPLOYEE_SERIALIZER] Validation des données: {data}")
        
        # Vérifier que tous les champs requis sont présents
        required_fields = ['first_name', 'last_name', 'email', 'department', 'position_title']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.error(f"[EMPLOYEE_SERIALIZER] Champs manquants: {missing_fields}")
            raise serializers.ValidationError({
                'error': 'Champs manquants',
                'missing_fields': missing_fields
            })
        
        return data
    
    def to_representation(self, instance):
        """Override pour ajouter l'URL complète de l'avatar dans la réponse"""
        try:
            data = super().to_representation(instance)
            
            # S'assurer que initials est toujours présent (fallback si problème)
            if 'initials' not in data or not data.get('initials'):
                try:
                    data['initials'] = instance.initials
                except Exception:
                    data['initials'] = "?"
            
            # S'assurer que full_name est toujours présent
            if 'full_name' not in data or not data.get('full_name'):
                try:
                    data['full_name'] = instance.full_name
                except Exception:
                    data['full_name'] = f"{instance.first_name or ''} {instance.last_name or ''}".strip() or "Sans nom"
            
            # avatar est déjà transformé en URL complète par get_avatar() dans SerializerMethodField
            # On ajoute aussi avatar_url pour compatibilité avec d'autres parties du code
            if 'avatar' in data and data['avatar']:
                data['avatar_url'] = data['avatar']
            
            return data
        except Exception as e:
            # Fallback en cas d'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[EMPLOYEE_SERIALIZER] Erreur dans to_representation pour {instance.id}: {e}")
            # Retourner au moins les données de base
            return {
                'id': instance.id,
                'first_name': instance.first_name or '',
                'last_name': instance.last_name or '',
                'full_name': instance.first_name or instance.last_name or 'Sans nom',
                'initials': '?',
                'email': instance.email or '',
            }
    
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
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'initials', 'email', 'phone_fixed', 'phone_mobile',
            'department', 'position_title', 'department_name',
            'avatar',
            'created_at', 'updated_at'
        ]
    
    def get_avatar(self, obj):
        """Retourne l'URL complète de l'avatar"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[AVATAR_SERIALIZER] === GESTION AVATAR POUR {obj.full_name} ===")
        logger.info(f"[AVATAR_SERIALIZER] Objet avatar: {obj.avatar}")
        logger.info(f"[AVATAR_SERIALIZER] Type avatar: {type(obj.avatar)}")
        
        if obj.avatar:
            logger.info(f"[AVATAR_SERIALIZER] Avatar trouvé:")
            logger.info(f"  - Nom: {obj.avatar.name}")
            logger.info(f"  - URL: {obj.avatar.url}")
            logger.info(f"  - Taille: {obj.avatar.size} bytes")
            logger.info(f"  - Chemin: {obj.avatar.path}")
            
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                logger.info(f"[AVATAR_SERIALIZER] URL générée avec request: {url}")
                return url
            else:
                logger.info(f"[AVATAR_SERIALIZER] Pas de request, utilisation du fallback")
                # Fallback si pas de request (ex: tests)
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
                url = f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
                logger.info(f"[AVATAR_SERIALIZER] URL fallback: {url}")
                return url
        else:
            logger.info(f"[AVATAR_SERIALIZER] Aucun avatar pour {obj.full_name}")
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
            'department', 'position_title', 'department_name',
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
