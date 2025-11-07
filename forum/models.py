from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Forum(models.Model):
    """
    Modèle pour représenter une catégorie de forum (ex: "Annonces Générales", "Support Technique")
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du forum",
        help_text="Nom de la catégorie de forum"
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Description de la catégorie de forum",
        blank=True
    )
    image = models.ImageField(
        upload_to='forums/',
        verbose_name="Image",
        help_text="Image représentative du forum",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Indique si le forum est actif et visible"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Forum"
        verbose_name_plural = "Forums"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        """Retourne le nombre de membres ayant participé au forum"""
        try:
            # Vérifier si le champ annoté existe (depuis un queryset annoté)
            # Les champs annotés sont stockés comme attributs
            if hasattr(self, 'annotated_member_count'):
                # C'est un champ annoté, retourner directement la valeur
                count = self.annotated_member_count
                logger.debug(f"📊 [FORUM_MODEL] member_count (annoté) pour Forum {self.id}: {count}")
                return count
            
            # Sinon, calculer via la propriété
            count = Conversation.objects.filter(forum=self).values('author').distinct().count()
            logger.debug(f"📊 [FORUM_MODEL] member_count (calculé) pour Forum {self.id}: {count}")
            return count
        except Exception as e:
            logger.error(f"❌ [FORUM_MODEL] Erreur member_count pour Forum {self.id}: {e}", exc_info=True)
            return 0
    
    @property
    def conversation_count(self):
        """Retourne le nombre de conversations dans le forum"""
        try:
            # Vérifier si le champ annoté existe (depuis un queryset annoté)
            if hasattr(self, 'annotated_conversation_count'):
                # C'est un champ annoté, retourner directement la valeur
                count = self.annotated_conversation_count
                logger.debug(f"📊 [FORUM_MODEL] conversation_count (annoté) pour Forum {self.id}: {count}")
                return count
            
            # Sinon, calculer via la propriété
            count = self.conversations.count()
            logger.debug(f"📊 [FORUM_MODEL] conversation_count (calculé) pour Forum {self.id}: {count}")
            return count
        except Exception as e:
            logger.error(f"❌ [FORUM_MODEL] Erreur conversation_count pour Forum {self.id}: {e}", exc_info=True)
            return 0


class Conversation(models.Model):
    """
    Modèle pour représenter une conversation (post) dans un forum
    """
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name="Forum",
        help_text="Forum auquel appartient cette conversation"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_conversations',
        verbose_name="Auteur",
        help_text="Utilisateur ayant créé cette conversation"
    )
    title = models.CharField(
        max_length=300,
        verbose_name="Titre",
        help_text="Titre de la conversation",
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Contenu détaillé de la conversation",
        blank=True,
        null=True
    )
    content = models.TextField(
        verbose_name="Contenu",
        help_text="Contenu de la conversation (utilisé pour créer rapidement)",
        blank=True,
        null=True
    )
    image = models.ImageField(
        upload_to='conversations/',
        verbose_name="Image",
        help_text="Image associée à la conversation",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Résolu",
        help_text="Indique si la conversation est résolue (pour les forums de support)"
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de vues",
        help_text="Nombre de fois que la conversation a été consultée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement title et description depuis content si nécessaire"""
        # Si content est fourni mais pas title/description, les générer automatiquement
        if self.content and not self.title:
            # Utiliser les premiers mots du contenu comme titre (max 300 caractères)
            content_preview = self.content.strip()
            if len(content_preview) > 300:
                # Prendre les 297 premiers caractères + "..."
                self.title = content_preview[:297] + "..."
            else:
                self.title = content_preview
        
        if self.content and not self.description:
            self.description = self.content.strip()
        
        # Si description est fournie mais pas title, utiliser les premiers mots de description
        if self.description and not self.title:
            desc_preview = self.description.strip()
            if len(desc_preview) > 300:
                self.title = desc_preview[:297] + "..."
            else:
                self.title = desc_preview
        
        # Si title est fourni mais pas description, utiliser title comme description
        if self.title and not self.description:
            self.description = self.title
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['forum', '-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        title_display = self.title if self.title else (self.content[:50] + "..." if self.content and len(self.content) > 50 else (self.content or "Sans titre"))
        return f"{title_display} - {self.forum.name}"
    
    @property
    def replies_count(self):
        """Retourne le nombre de commentaires (réponses) dans la conversation"""
        return self.comments.count()
    
    def increment_views(self):
        """Incrémente le compteur de vues"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class Comment(models.Model):
    """
    Modèle pour représenter un commentaire (réponse) sur une conversation
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Conversation",
        help_text="Conversation à laquelle appartient ce commentaire"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_comments',
        verbose_name="Auteur",
        help_text="Utilisateur ayant créé ce commentaire"
    )
    content = models.TextField(
        verbose_name="Contenu",
        help_text="Contenu du commentaire"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Commentaire de {self.author.get_full_name()} sur {self.conversation.title[:50]}"
    
    @property
    def likes_count(self):
        """Retourne le nombre de likes sur ce commentaire"""
        return self.likes.count()


class CommentLike(models.Model):
    """
    Modèle pour représenter un like sur un commentaire
    Permet de gérer les likes/unlikes des utilisateurs
    """
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name="Commentaire",
        help_text="Commentaire liké"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_comment_likes',
        verbose_name="Utilisateur",
        help_text="Utilisateur ayant liké le commentaire"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Like de commentaire"
        verbose_name_plural = "Likes de commentaires"
        unique_together = ['comment', 'user']  # Un utilisateur ne peut liker qu'une fois
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} aime le commentaire #{self.comment.id}"
