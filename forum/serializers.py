from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Forum, ForumMessage

User = get_user_model()


class UserInfoSerializer(serializers.ModelSerializer):
    """Serializer pour les informations de base d'un utilisateur"""
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                  'avatar', 'avatar_url', 'position', 'department']
    
    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            base_url = getattr(settings, 'BASE_URL', '')
            return f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
        return None
    
    def get_department(self, obj):
        """Retourne le nom du département"""
        if obj.department:
            return obj.department.name
        return None


class ForumMessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages de forum"""
    author_info = UserInfoSerializer(source='author', read_only=True)
    
    class Meta:
        model = ForumMessage
        fields = ['id', 'forum', 'author', 'author_info', 'content', 
                  'created_at', 'updated_at', 'is_edited']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_edited']


class ForumMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de messages"""
    
    class Meta:
        model = ForumMessage
        fields = ['content']
    
    def validate_content(self, value):
        """Valide que le contenu n'est pas vide"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le contenu du message ne peut pas être vide.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le message doit contenir au moins 3 caractères.")
        return value.strip()


class ForumSerializer(serializers.ModelSerializer):
    """Serializer pour les forums avec statistiques"""
    created_by_info = UserInfoSerializer(source='created_by', read_only=True)
    message_count = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Forum
        fields = ['id', 'title', 'image', 'image_url', 'created_by', 'created_by_info',
                  'is_active', 'created_at', 'updated_at',
                  'message_count', 'participant_count', 'last_message']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'image_url']
    
    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image du forum"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            base_url = getattr(settings, 'BASE_URL', '')
            return f"{base_url}{settings.MEDIA_URL}{obj.image.name}"
        return None
    
    def get_message_count(self, obj):
        """Retourne le nombre de messages"""
        return obj.get_message_count()
    
    def get_participant_count(self, obj):
        """Retourne le nombre de participants"""
        return obj.get_participant_count()
    
    def get_last_message(self, obj):
        """Retourne les informations du dernier message"""
        last_msg = obj.get_last_message()
        if last_msg:
            return {
                'created_at': last_msg.created_at.isoformat(),
                'author': last_msg.author.get_full_name() or last_msg.author.username
            }
        return None


class ForumCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de forums"""
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Forum
        fields = ['title', 'image']
    
    def validate_title(self, value):
        """Valide le titre"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le titre du forum ne peut pas être vide.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le titre doit contenir au moins 3 caractères.")
        if len(value.strip()) > 200:
            raise serializers.ValidationError("Le titre ne peut pas dépasser 200 caractères.")
        return value.strip()
    
    def validate_image(self, value):
        """Valide l'image"""
        if value:
            # Vérifier le type de fichier
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Le fichier doit être une image.")
            # Vérifier la taille (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La taille de l'image ne doit pas dépasser 5MB.")
        return value

