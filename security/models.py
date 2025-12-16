from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import os

User = get_user_model()

def security_document_upload_path(instance, filename):
    """Génère le chemin d'upload pour les documents de sécurité"""
    # Organiser par année/mois pour éviter trop de fichiers dans un dossier
    now = timezone.now()
    year = now.year
    month = now.month
    return f'security/{year}/{month}/{filename}'

class SecurityDocument(models.Model):
    """
    Modèle pour stocker les documents de sécurité (PDFs et images)
    """
    # Informations de base
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du document",
        help_text="Nom du document (ex: Règlement Intérieur, Guide de Sécurité)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du document affichée sur la carte"
    )
    
    # Fichier (PDF ou image)
    file = models.FileField(
        upload_to=security_document_upload_path,
        verbose_name="Fichier",
        help_text="Fichier PDF ou image (JPG, PNG, GIF, WEBP) à uploader"
    )
    
    # Icône pour l'affichage (nom de l'icône Lucide React)
    icon = models.CharField(
        max_length=50,
        default="file-text",
        verbose_name="Icône",
        help_text="Nom de l'icône Lucide React (ex: file-text, shield, book-open, file-check)"
    )
    
    # Métadonnées
    file_size = models.PositiveIntegerField(
        verbose_name="Taille du fichier (bytes)",
        help_text="Taille du fichier en octets"
    )
    
    # Utilisateur qui a uploadé
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_security_documents',
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
    
    # Ordre d'affichage
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Ordre d'affichage des cartes (0 = premier)"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Document actif (visible sur la page)"
    )
    
    class Meta:
        verbose_name = "Document de sécurité"
        verbose_name_plural = "Documents de sécurité"
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_file_size_display(self):
        """Retourne la taille du fichier formatée"""
        size = self.file_size
        if size is None:
            return "N/A"
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
    
    def is_image(self):
        """Vérifie si le fichier est une image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return self.get_file_extension() in image_extensions
    
    def get_file_type(self):
        """Retourne le type de fichier: 'pdf' ou 'image'"""
        if self.is_pdf():
            return 'pdf'
        elif self.is_image():
            return 'image'
        return 'other'
    
    def get_absolute_url(self):
        """Retourne l'URL du fichier"""
        if self.file:
            return self.file.url
        return None
