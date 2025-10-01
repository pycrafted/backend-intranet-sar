from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
import os

User = get_user_model()

class DocumentCategory(models.Model):
    """
    Modèle pour les catégories de documents (services)
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la catégorie",
        help_text="Nom du service ou de la catégorie"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description de la catégorie"
    )
    
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name="Couleur",
        help_text="Couleur hexadécimale pour l'affichage"
    )
    
    icon = models.CharField(
        max_length=50,
        default="file",
        verbose_name="Icône",
        help_text="Nom de l'icône (Lucide React)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Catégorie active"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre",
        help_text="Ordre d'affichage"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Catégorie de document"
        verbose_name_plural = "Catégories de documents"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class DocumentFolder(models.Model):
    """
    Modèle pour les dossiers de documents (structure hiérarchique)
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Nom du dossier",
        help_text="Nom du dossier"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description optionnelle du dossier"
    )
    
    # Dossier parent pour créer une hiérarchie
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Dossier parent",
        help_text="Dossier parent (null pour la racine)"
    )
    
    # Couleur et icône pour l'affichage
    color = models.CharField(
        max_length=7,
        default="#6B7280",
        verbose_name="Couleur",
        help_text="Couleur hexadécimale pour l'affichage"
    )
    
    icon = models.CharField(
        max_length=50,
        default="folder",
        verbose_name="Icône",
        help_text="Nom de l'icône (Lucide React)"
    )
    
    # Utilisateur qui a créé le dossier
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_folders',
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le dossier"
    )
    
    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Dossier actif (visible par tous)"
    )
    
    class Meta:
        verbose_name = "Dossier de documents"
        verbose_name_plural = "Dossiers de documents"
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name
    
    def get_full_path(self):
        """Retourne le chemin complet du dossier"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return self.name
    
    def get_depth(self):
        """Retourne la profondeur du dossier dans la hiérarchie"""
        if self.parent:
            return self.parent.get_depth() + 1
        return 0
    
    def get_children_count(self):
        """Retourne le nombre de dossiers enfants"""
        return self.children.filter(is_active=True).count()
    
    def get_documents_count(self):
        """Retourne le nombre de documents dans ce dossier"""
        return self.documents.filter(is_active=True).count()
    
    def get_total_documents_count(self):
        """Retourne le nombre total de documents (dossier + sous-dossiers)"""
        count = self.get_documents_count()
        for child in self.children.filter(is_active=True):
            count += child.get_total_documents_count()
        return count
    
    def clean(self):
        """Validation personnalisée"""
        # Empêcher les références circulaires
        if self.parent and self.parent == self:
            raise ValidationError("Un dossier ne peut pas être son propre parent")
        
        # Vérifier la profondeur maximale (éviter les hiérarchies trop profondes)
        if self.parent and self.parent.get_depth() >= 10:
            raise ValidationError("La hiérarchie des dossiers ne peut pas dépasser 10 niveaux")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

def document_upload_path(instance, filename):
    """Génère le chemin d'upload pour les documents"""
    # Organiser par année/mois pour éviter trop de fichiers dans un dossier
    now = timezone.now()
    year = now.year
    month = now.month
    return f'documents/{year}/{month}/{filename}'

class Document(models.Model):
    """
    Modèle pour stocker les documents PDF
    """
    # Informations de base
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du document",
        help_text="Nom du document"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description optionnelle du document"
    )
    
    # Fichier PDF
    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name="Fichier PDF",
        help_text="Fichier PDF à uploader"
    )
    
    # Catégorie du document
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Catégorie",
        help_text="Service ou catégorie du document"
    )
    
    # Dossier contenant le document
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name="Dossier",
        help_text="Dossier contenant le document"
    )
    
    # Métadonnées
    file_size = models.PositiveIntegerField(
        verbose_name="Taille du fichier (bytes)",
        help_text="Taille du fichier en octets"
    )
    
    # Utilisateur qui a uploadé
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name="Uploadé par",
        help_text="Utilisateur qui a uploadé le document"
    )
    
    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    # Statistiques
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de téléchargements",
        help_text="Compteur de téléchargements"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Document actif (visible par tous)"
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.uploaded_by.get_full_name()})"
    
    def get_file_size_display(self):
        """Retourne la taille du fichier formatée"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def get_file_extension(self):
        """Retourne l'extension du fichier"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    def is_pdf(self):
        """Vérifie si le fichier est un PDF"""
        return self.get_file_extension() == '.pdf'
    
    def increment_download_count(self):
        """Incrémente le compteur de téléchargements"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def get_absolute_url(self):
        """Retourne l'URL du fichier"""
        if self.file:
            return self.file.url
        return None