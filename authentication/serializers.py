from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from django.contrib.auth.models import Group


class DepartmentNestedSerializer(serializers.Serializer):
    """Serializer imbriqué pour le département (lecture seule)"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class ManagerNestedSerializer(serializers.Serializer):
    """Serializer imbriqué pour le manager (lecture seule)"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    matricule = serializers.CharField(read_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour afficher les informations utilisateur"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    office_phone = serializers.CharField(source='phone_fixed', read_only=True)
    department = DepartmentNestedSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    manager = ManagerNestedSerializer(read_only=True)
    manager_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)
    groups_names = serializers.SerializerMethodField()
    is_admin_group = serializers.SerializerMethodField()
    is_communication_group = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'matricule',
            'position', 'phone_number', 'phone_fixed', 'office_phone', 'department', 'department_id',
            'manager', 'manager_id',
            'avatar', 'avatar_url',
            'is_active', 'is_staff', 'is_superuser', 
            'groups_names', 'is_admin_group', 'is_communication_group',
            'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined']
    
    def get_avatar_url(self, obj):
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

    def get_groups_names(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def get_is_admin_group(self, obj):
        return obj.groups.filter(name__iexact='administrateur').exists()

    def get_is_communication_group(self, obj):
        return obj.groups.filter(name__iexact='communication').exists()
    
    def update(self, instance, validated_data):
        """Override pour gérer department_id et manager_id"""
        if 'department_id' in validated_data:
            department_id = validated_data.pop('department_id')
            if department_id is not None:
                from annuaire.models import Department
                try:
                    department = Department.objects.get(id=department_id)
                    validated_data['department'] = department
                except Department.DoesNotExist:
                    raise serializers.ValidationError({'department_id': 'Département introuvable.'})
            else:
                validated_data['department'] = None
        
        if 'manager_id' in validated_data:
            manager_id = validated_data.pop('manager_id')
            if manager_id is not None:
                try:
                    manager = User.objects.get(id=manager_id)
                    # Empêcher un utilisateur d'être son propre manager
                    if manager.id == instance.id:
                        raise serializers.ValidationError({'manager_id': 'Un utilisateur ne peut pas être son propre manager.'})
                    validated_data['manager'] = manager
                except User.DoesNotExist:
                    raise serializers.ValidationError({'manager_id': 'Manager introuvable.'})
            else:
                validated_data['manager'] = None
        
        return super().update(instance, validated_data)


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion utilisateur"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            if not user.check_password(password):
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            if not user.is_active:
                raise serializers.ValidationError('Ce compte a été désactivé.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Email et mot de passe requis.')


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Un utilisateur avec cet email existe déjà.')
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('Les mots de passe ne correspondent pas.')
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        email = validated_data['email']
        username = email.split('@')[0]
        
        user = User.objects.create_user(username=username, password=password, **validated_data)
        # Assigner par défaut le groupe "utilisateur simple"
        try:
            default_group, _ = Group.objects.get_or_create(name="utilisateur simple")
            user.groups.add(default_group)
        except Exception:
            # Ne pas bloquer la création si le groupe n'existe pas encore
            pass
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil utilisateur"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    office_phone = serializers.CharField(source='phone_fixed', read_only=False)
    department = DepartmentNestedSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    manager = ManagerNestedSerializer(read_only=True)
    manager_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)
    
    groups_names = serializers.SerializerMethodField(read_only=True)
    is_admin_group = serializers.SerializerMethodField(read_only=True)
    is_communication_group = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'matricule',
            'position', 'phone_number', 'phone_fixed', 'office_phone', 'department', 'department_id',
            'manager', 'manager_id',
            'avatar', 'avatar_url',
            'is_active', 'is_staff', 'is_superuser', 
            'groups_names', 'is_admin_group', 'is_communication_group',
            'last_login', 'date_joined'
        ]
        read_only_fields = [
            'id', 'is_active', 'is_staff', 'is_superuser',
            'last_login', 'date_joined'
        ]
    
    def get_avatar_url(self, obj):
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

    def get_groups_names(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def get_is_admin_group(self, obj):
        return obj.groups.filter(name__iexact='administrateur').exists()

    def get_is_communication_group(self, obj):
        return obj.groups.filter(name__iexact='communication').exists()
    
    def update(self, instance, validated_data):
        # Gérer office_phone qui mappe vers phone_fixed
        if 'office_phone' in validated_data:
            validated_data['phone_fixed'] = validated_data.pop('office_phone')
        
        # Gérer department_id qui mappe vers department
        if 'department_id' in validated_data:
            department_id = validated_data.pop('department_id')
            if department_id is not None:
                from annuaire.models import Department
                try:
                    department = Department.objects.get(id=department_id)
                    validated_data['department'] = department
                except Department.DoesNotExist:
                    raise serializers.ValidationError({'department_id': 'Département introuvable.'})
            else:
                validated_data['department'] = None
        
        # Gérer manager_id qui mappe vers manager
        if 'manager_id' in validated_data:
            manager_id = validated_data.pop('manager_id')
            if manager_id is not None:
                try:
                    manager = User.objects.get(id=manager_id)
                    # Empêcher un utilisateur d'être son propre manager
                    if manager.id == instance.id:
                        raise serializers.ValidationError({'manager_id': 'Un utilisateur ne peut pas être son propre manager.'})
                    validated_data['manager'] = manager
                except User.DoesNotExist:
                    raise serializers.ValidationError({'manager_id': 'Manager introuvable.'})
            else:
                validated_data['manager'] = None
        
        return super().update(instance, validated_data)

