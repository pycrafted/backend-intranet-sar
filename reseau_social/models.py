from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """
    Modèle pour représenter une conversation entre utilisateurs
    Supporte les conversations individuelles (1-1) et de groupe
    """
    TYPE_CHOICES = [
        ('direct', 'Conversation directe'),
        ('group', 'Conversation de groupe'),
    ]
    
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='direct')
    name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Nom de la conversation (pour les groupes uniquement)'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_conversations',
        help_text='Utilisateur ayant créé la conversation'
    )
    participants = models.ManyToManyField(
        User,
        through='Participant',
        related_name='conversations',
        help_text='Participants à la conversation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        indexes = [
            models.Index(fields=['-last_message_at']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        if self.type == 'group' and self.name:
            return f"Groupe: {self.name}"
        return f"Conversation #{self.id}"
    
    def update_last_message_at(self):
        """Met à jour la date du dernier message (en excluant les messages supprimés)"""
        last_message = self.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_message:
            self.last_message_at = last_message.created_at
            self.save(update_fields=['last_message_at'])
        else:
            # Si aucun message non supprimé, mettre à None ou garder la dernière date
            self.last_message_at = None
            self.save(update_fields=['last_message_at'])
    
    def get_display_name(self, user):
        """Retourne le nom d'affichage de la conversation pour un utilisateur donné"""
        if self.type == 'group' and self.name:
            return self.name
        # Pour les conversations directes, retourner le nom de l'autre participant
        other_participants = self.participants.exclude(id=user.id)
        if other_participants.exists():
            other = other_participants.first()
            return other.get_full_name() or other.username
        return "Conversation"


class Participant(models.Model):
    """
    Modèle intermédiaire pour la relation Many-to-Many entre User et Conversation
    Permet de stocker des métadonnées spécifiques à chaque participant
    """
    ROLE_CHOICES = [
        ('member', 'Membre'),
        ('admin', 'Administrateur'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='conversation_participants'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_participations'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    unread_count = models.IntegerField(default=0)
    last_read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
        verbose_name = "Participant"
        verbose_name_plural = "Participants"
        indexes = [
            models.Index(fields=['conversation', 'user']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} dans {self.conversation}"


class Message(models.Model):
    """
    Modèle pour représenter un message dans une conversation
    Supporte les messages texte et les messages avec pièces jointes
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Message texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
        ('system', 'Message système'),
    ]
    
    id = models.AutoField(primary_key=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text='Conversation à laquelle appartient le message'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        help_text='Utilisateur ayant envoyé le message'
    )
    content = models.TextField(help_text='Contenu du message')
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        help_text='Type de message'
    )
    attachment = models.FileField(
        upload_to='messages/attachments/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Pièce jointe du message'
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text='Message auquel répond ce message'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        sender_name = self.sender.username if self.sender else "Système"
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Message de {sender_name}: {preview}"
    
    def soft_delete(self):
        """Suppression douce du message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
        # Mettre à jour le dernier message de la conversation si ce message était le dernier
        if self.conversation.last_message_at == self.created_at:
            self.conversation.update_last_message_at()


class MessageRead(models.Model):
    """
    Modèle pour tracker les messages lus par chaque utilisateur
    Permet de déterminer quels messages ont été lus par qui
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_by_users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='read_messages'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        verbose_name = "Message lu"
        verbose_name_plural = "Messages lus"
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['user', '-read_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} a lu le message #{self.message.id}"
