from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
import os

User = get_user_model()


def forum_image_upload_path(instance, filename):
    """
    Fonction pour générer le chemin d'upload des images de forum
    Format: forums/{year}/{month}/{filename}
    """
    now = timezone.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # Extraire l'extension du fichier
    ext = filename.split('.')[-1]
    # Générer un nom de fichier unique basé sur l'ID du forum et un timestamp
    # Si l'instance n'a pas encore d'ID, utiliser un timestamp
    if instance.id:
        filename = f"forum_{instance.id}_{int(now.timestamp())}.{ext}"
    else:
        filename = f"forum_{int(now.timestamp())}.{ext}"
    
    return f'forums/{year}/{month}/{filename}'


def forum_message_image_upload_path(instance, filename):
    """
    Fonction pour générer le chemin d'upload des images de messages de forum
    Format: forum_messages/{year}/{month}/{filename}
    """
    now = timezone.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # Extraire l'extension du fichier
    ext = filename.split('.')[-1]
    # Générer un nom de fichier unique basé sur l'ID du message et un timestamp
    if instance.id:
        filename = f"message_{instance.id}_{int(now.timestamp())}.{ext}"
    else:
        filename = f"message_{int(now.timestamp())}.{ext}"
    
    return f'forum_messages/{year}/{month}/{filename}'


class Forum(models.Model):
    """
    Modèle pour représenter un forum de discussion
    """
    title = models.CharField(
        max_length=200,
        verbose_name="Titre",
        help_text="Titre du forum"
    )
    
    image = models.ImageField(
        upload_to=forum_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Image du forum",
        help_text="Image d'identité du forum affichée en haut"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_forums',
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le forum"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Indique si le forum est actif"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Forum"
        verbose_name_plural = "Forums"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_message_count(self):
        """Retourne le nombre total de messages dans ce forum"""
        return self.messages.count()
    
    def get_participant_count(self):
        """Retourne le nombre de participants uniques dans ce forum"""
        return self.messages.values('author').distinct().count()
    
    def get_last_message(self):
        """Retourne le dernier message posté dans ce forum"""
        return self.messages.order_by('-created_at').first()


class ForumMessage(models.Model):
    """
    Modèle pour représenter un message dans un forum
    """
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Forum",
        help_text="Forum auquel appartient ce message"
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_messages',
        verbose_name="Auteur",
        help_text="Auteur du message"
    )
    
    content = models.TextField(
        blank=True,
        verbose_name="Contenu",
        help_text="Contenu du message"
    )
    
    image = models.ImageField(
        upload_to=forum_message_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Image du message",
        help_text="Image attachée au message"
    )
    
    is_edited = models.BooleanField(
        default=False,
        verbose_name="Modifié",
        help_text="Indique si le message a été modifié"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Message de forum"
        verbose_name_plural = "Messages de forum"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['forum', '-created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Message #{self.id} - {self.forum.title} - {self.author.username}"
    
    def can_edit(self, user):
        """Vérifie si l'utilisateur peut modifier ce message"""
        return self.author == user
    
    def can_delete(self, user):
        """Vérifie si l'utilisateur peut supprimer ce message"""
        return self.author == user or self.forum.created_by == user
