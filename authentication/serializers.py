from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher les informations utilisateur (version simplifiée)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    manager_info = serializers.SerializerMethodField()
    is_google_connected = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'avatar', 'avatar_url', 'phone_number', 'office_phone', 'position', 'department', 'matricule', 'manager', 'manager_info', 'is_active', 'is_staff', 'is_superuser', 
            'last_login', 'created_at', 'updated_at',
            # Champs OAuth Google
            'google_id', 'google_email', 'google_avatar_url', 'is_google_connected'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at', 'is_google_connected']
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_manager_info(self, obj):
        """Retourne les informations du manager"""
        if obj.manager:
            return {
                'id': obj.manager.id,
                'first_name': obj.manager.first_name,
                'last_name': obj.manager.last_name,
                'full_name': obj.manager.get_full_name(),
                'position': obj.manager.position,
                'department': obj.manager.department
            }
        return None
    
    def get_is_google_connected(self, obj):
        """Retourne si l'utilisateur est connecté via Google"""
        return obj.is_google_connected()


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion utilisateur
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Trouver l'utilisateur par email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            # Vérifier le mot de passe
            if not user.check_password(password):
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            # Vérifier si le compte est actif
            if not user.is_active:
                raise serializers.ValidationError('Ce compte a été désactivé.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Email et mot de passe requis.')


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur (version simplifiée)
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number', 'office_phone', 'position', 'department', 'matricule', 'manager', 'password', 'password_confirm'
        ]
    
    def validate_email(self, value):
        """Vérifier que l'email est unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Un utilisateur avec cet email existe déjà.')
        return value
    
    def validate_matricule(self, value):
        """Vérifier que le matricule est unique"""
        if value and User.objects.filter(matricule=value).exists():
            raise serializers.ValidationError('Un utilisateur avec ce matricule existe déjà.')
        return value
    
    def validate_phone_number(self, value):
        """Valider le format du numéro de téléphone personnel"""
        if value:
            # Supprimer les espaces et caractères spéciaux
            phone = re.sub(r'[^\d+]', '', value)
            # Vérifier que le numéro contient au moins 8 chiffres
            if len(phone) < 8:
                raise serializers.ValidationError('Le numéro de téléphone doit contenir au moins 8 chiffres.')
            # Vérifier qu'il ne contient que des chiffres et éventuellement un + au début
            if not re.match(r'^\+?[\d]+$', phone):
                raise serializers.ValidationError('Le numéro de téléphone ne peut contenir que des chiffres et éventuellement un + au début.')
        return value
    
    def validate_office_phone(self, value):
        """Valider le format du numéro de téléphone fixe"""
        if value:
            # Supprimer les espaces et caractères spéciaux
            phone = re.sub(r'[^\d+]', '', value)
            # Vérifier que le numéro contient au moins 8 chiffres
            if len(phone) < 8:
                raise serializers.ValidationError('Le numéro de téléphone fixe doit contenir au moins 8 chiffres.')
            # Vérifier qu'il ne contient que des chiffres et éventuellement un + au début
            if not re.match(r'^\+?[\d]+$', phone):
                raise serializers.ValidationError('Le numéro de téléphone fixe ne peut contenir que des chiffres et éventuellement un + au début.')
        return value
    
    def validate(self, attrs):
        """Vérifier que les mots de passe correspondent"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('Les mots de passe ne correspondent pas.')
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur avec des valeurs par défaut"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Générer un username unique basé sur l'email
        email = validated_data['email']
        username = email.split('@')[0]
        base_username = username
        
        # S'assurer que le username est unique
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            is_active=True,
            password=password,
            **validated_data
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour du profil utilisateur (version simplifiée)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'avatar', 'avatar_url', 'phone_number', 'office_phone', 'position', 'department', 'matricule', 'manager', 'is_active', 'is_staff', 'is_superuser', 
            'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'is_active', 'is_staff', 'is_superuser',
            'last_login', 'created_at', 'updated_at'
        ]
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def validate_email(self, value):
        """Vérifier que l'email est unique (sauf pour l'utilisateur actuel)"""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError('Un utilisateur avec cet email existe déjà.')
        return value
    
    def validate_matricule(self, value):
        """Vérifier que le matricule est unique (sauf pour l'utilisateur actuel)"""
        if value:
            user = self.context['request'].user
            if User.objects.filter(matricule=value).exclude(id=user.id).exists():
                raise serializers.ValidationError('Un utilisateur avec ce matricule existe déjà.')
        return value
    
    def validate_phone_number(self, value):
        """Valider le format du numéro de téléphone personnel"""
        if value:
            # Supprimer les espaces et caractères spéciaux
            phone = re.sub(r'[^\d+]', '', value)
            # Vérifier que le numéro contient au moins 8 chiffres
            if len(phone) < 8:
                raise serializers.ValidationError('Le numéro de téléphone doit contenir au moins 8 chiffres.')
            # Vérifier qu'il ne contient que des chiffres et éventuellement un + au début
            if not re.match(r'^\+?[\d]+$', phone):
                raise serializers.ValidationError('Le numéro de téléphone ne peut contenir que des chiffres et éventuellement un + au début.')
        return value
    
    def validate_office_phone(self, value):
        """Valider le format du numéro de téléphone fixe"""
        if value:
            # Supprimer les espaces et caractères spéciaux
            phone = re.sub(r'[^\d+]', '', value)
            # Vérifier que le numéro contient au moins 8 chiffres
            if len(phone) < 8:
                raise serializers.ValidationError('Le numéro de téléphone fixe doit contenir au moins 8 chiffres.')
            # Vérifier qu'il ne contient que des chiffres et éventuellement un + au début
            if not re.match(r'^\+?[\d]+$', phone):
                raise serializers.ValidationError('Le numéro de téléphone fixe ne peut contenir que des chiffres et éventuellement un + au début.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """Vérifier l'ancien mot de passe"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Ancien mot de passe incorrect.')
        return value
    
    def validate(self, attrs):
        """Vérifier que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('Les nouveaux mots de passe ne correspondent pas.')
        return attrs
    
    def save(self):
        """Changer le mot de passe"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la liste des utilisateurs (version simplifiée)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'avatar_url', 'phone_number', 'position', 'matricule', 'is_active', 'is_staff', 'is_superuser', 'last_login'
        ]
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


