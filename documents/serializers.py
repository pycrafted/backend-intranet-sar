from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Document, DocumentCategory, DocumentFolder

User = get_user_model()

class DocumentCategorySerializer(serializers.ModelSerializer):
    """
    Serializer pour les catégories de documents
    """
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'description', 'color', 'icon', 'order']

class DocumentFolderSerializer(serializers.ModelSerializer):
    """
    Serializer pour les dossiers de documents
    """
    # Champs calculés
    full_path = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    total_documents_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFolder
        fields = [
            'id',
            'name',
            'description',
            'parent',
            'parent_name',
            'color',
            'icon',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'is_active',
            'full_path',
            'depth',
            'children_count',
            'documents_count',
            'total_documents_count',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'full_path',
            'depth',
            'children_count',
            'documents_count',
            'total_documents_count',
        ]
    
    def get_full_path(self, obj):
        """Retourne le chemin complet du dossier"""
        return obj.get_full_path()
    
    def get_depth(self, obj):
        """Retourne la profondeur du dossier"""
        return obj.get_depth()
    
    def get_children_count(self, obj):
        """Retourne le nombre de dossiers enfants"""
        return obj.get_children_count()
    
    def get_documents_count(self, obj):
        """Retourne le nombre de documents dans ce dossier"""
        return obj.get_documents_count()
    
    def get_total_documents_count(self, obj):
        """Retourne le nombre total de documents (dossier + sous-dossiers)"""
        return obj.get_total_documents_count()
    
    def get_created_by_name(self, obj):
        """Retourne le nom de l'utilisateur qui a créé le dossier"""
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_parent_name(self, obj):
        """Retourne le nom du dossier parent"""
        return obj.parent.name if obj.parent else None
    
    def create(self, validated_data):
        """Création d'un nouveau dossier"""
        # L'utilisateur est ajouté dans la vue
        folder = super().create(validated_data)
        return folder

class DocumentFolderTreeSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'arbre des dossiers (avec enfants)
    """
    children = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFolder
        fields = [
            'id',
            'name',
            'description',
            'color',
            'icon',
            'children',
            'documents_count',
        ]
    
    def get_children(self, obj):
        """Retourne les dossiers enfants"""
        children = obj.children.filter(is_active=True).order_by('name')
        return DocumentFolderTreeSerializer(children, many=True).data
    
    def get_documents_count(self, obj):
        """Retourne le nombre de documents dans ce dossier"""
        return obj.get_documents_count()

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les documents
    """
    # Champs calculés
    file_size_display = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    is_pdf = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    category_info = serializers.SerializerMethodField()
    folder_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'file',
            'file_size',
            'file_size_display',
            'file_extension',
            'is_pdf',
            'file_url',
            'uploaded_by',
            'uploaded_by_name',
            'category',
            'category_info',
            'folder',
            'folder_info',
            'created_at',
            'updated_at',
            'download_count',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'file_size_display',
            'file_extension',
            'is_pdf',
            'file_url',
            'uploaded_by',
            'uploaded_by_name',
            'created_at',
            'updated_at',
            'download_count',
        ]
    
    def get_file_size_display(self, obj):
        """Retourne la taille formatée"""
        return obj.get_file_size_display()
    
    def get_file_extension(self, obj):
        """Retourne l'extension du fichier"""
        return obj.get_file_extension()
    
    def get_is_pdf(self, obj):
        """Vérifie si c'est un PDF"""
        return obj.is_pdf()
    
    def get_uploaded_by_name(self, obj):
        """Retourne le nom de l'utilisateur qui a uploadé"""
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
    
    def get_file_url(self, obj):
        """Retourne l'URL du fichier"""
        return obj.get_absolute_url()
    
    def get_category_info(self, obj):
        """Retourne les informations de la catégorie"""
        if obj.category:
            return DocumentCategorySerializer(obj.category).data
        return None
    
    def get_folder_info(self, obj):
        """Retourne les informations du dossier"""
        if obj.folder:
            return DocumentFolderSerializer(obj.folder).data
        return None
    
    def validate_file(self, value):
        """Validation du fichier uploadé"""
        if not value:
            raise serializers.ValidationError("Aucun fichier fourni")
        
        # Vérifier l'extension
        allowed_extensions = ['.pdf']
        file_extension = value.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Seuls les fichiers PDF sont autorisés. Extension reçue: .{file_extension}"
            )
        
        # Vérifier la taille (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux. Taille maximale: {max_size / (1024*1024):.1f}MB"
            )
        
        return value
    
    def create(self, validated_data):
        """Création d'un nouveau document"""
        print(f"🔍 [SERIALIZER_CREATE] Données validées: {validated_data}")
        print(f"🔍 [SERIALIZER_CREATE] Utilisateur: {self.context['request'].user}")
        
        # L'utilisateur et file_size sont déjà ajoutés dans la vue
        document = super().create(validated_data)
        print(f"✅ [SERIALIZER_CREATE] Document créé: {document.id}")
        return document

class DocumentListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la liste des documents
    """
    file_size_display = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'file_size_display',
            'file_extension',
            'file_url',
            'uploaded_by_name',
            'created_at',
            'download_count',
        ]
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    
    def get_file_extension(self, obj):
        return obj.get_file_extension()
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
    
    def get_file_url(self, obj):
        return obj.get_absolute_url()

class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer spécialement pour l'upload
    """
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'category', 'folder']
    
    def validate_file(self, value):
        """Validation stricte pour l'upload"""
        if not value:
            raise serializers.ValidationError("Aucun fichier fourni")
        
        # Vérifier que c'est un PDF
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont autorisés")
        
        # Vérifier la taille
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux. Taille maximale: {max_size / (1024*1024):.1f}MB"
            )
        
        return value
