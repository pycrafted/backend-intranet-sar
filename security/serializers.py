from rest_framework import serializers
from .models import SecurityDocument

class SecurityDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les documents de sécurité
    """
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()
    is_pdf = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityDocument
        fields = [
            'id',
            'title',
            'description',
            'file',
            'file_url',
            'file_size',
            'file_size_display',
            'file_type',
            'is_image',
            'is_pdf',
            'icon',
            'order',
            'uploaded_by',
            'uploaded_by_name',
            'created_at',
            'updated_at',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'file_url',
            'file_size_display',
            'file_type',
            'is_image',
            'is_pdf',
            'uploaded_by',
            'uploaded_by_name',
            'created_at',
            'updated_at',
        ]
    
    def get_file_url(self, obj):
        """Retourne l'URL complète du fichier"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_display(self, obj):
        """Retourne la taille formatée"""
        return obj.get_file_size_display()
    
    def get_uploaded_by_name(self, obj):
        """Retourne le nom de l'utilisateur qui a uploadé"""
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None
    
    def get_file_type(self, obj):
        """Retourne le type de fichier"""
        return obj.get_file_type()
    
    def get_is_image(self, obj):
        """Retourne True si le fichier est une image"""
        return obj.is_image()
    
    def get_is_pdf(self, obj):
        """Retourne True si le fichier est un PDF"""
        return obj.is_pdf()

class SecurityDocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer spécialement pour l'upload
    """
    class Meta:
        model = SecurityDocument
        fields = ['title', 'description', 'file', 'icon', 'order']
    
    def validate_file(self, value):
        """Validation pour l'upload"""
        if not value:
            raise serializers.ValidationError("Aucun fichier fourni")
        
        # Vérifier la taille (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux. Taille maximale: {max_size / (1024*1024):.1f}MB"
            )
        
        # Accepter les PDFs et les images
        file_extension = '.' + value.name.split('.')[-1].lower() if '.' in value.name else ''
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp']
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé. Extensions acceptées: {', '.join(allowed_extensions)}"
            )
        
        # Tronquer le nom du fichier si trop long (max 100 caractères avec extension)
        max_filename_length = 100
        if len(value.name) > max_filename_length:
            import os
            name, ext = os.path.splitext(value.name)
            # Tronquer le nom en gardant l'extension
            max_name_length = max_filename_length - len(ext)
            if max_name_length > 0:
                truncated_name = name[:max_name_length]
                new_filename = truncated_name + ext
                # Modifier le nom du fichier directement
                value.name = new_filename
            else:
                # Si l'extension seule dépasse 100 caractères, tronquer l'extension aussi
                value.name = name[:max_filename_length]
        
        return value

