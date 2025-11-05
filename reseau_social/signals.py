from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, Conversation


@receiver(post_save, sender=Message)
def update_conversation_on_message(sender, instance, created, **kwargs):
    """Met à jour la conversation lorsqu'un message est créé"""
    if created and not instance.is_deleted:
        conversation = instance.conversation
        conversation.update_last_message_at()
        conversation.save(update_fields=['last_message_at', 'updated_at'])


@receiver(pre_save, sender=Message)
def set_edited_flag(sender, instance, **kwargs):
    """Marque le message comme édité s'il a été modifié"""
    if instance.pk:
        try:
            old_instance = Message.objects.get(pk=instance.pk)
            if old_instance.content != instance.content:
                instance.is_edited = True
        except Message.DoesNotExist:
            pass



