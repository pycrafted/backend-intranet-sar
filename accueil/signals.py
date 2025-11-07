import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@receiver(post_save, sender='accueil.Idea')
def vectorize_idea_on_save(sender, instance, created, **kwargs):
    """
    Vectoriser automatiquement une idée lors de sa création ou modification
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.services.vectorization_service import VectorizationService
        from rag.models import DocumentEmbedding
        
        vectorization_service = VectorizationService()
        
        # Supprimer l'ancien embedding s'il existe (pour les mises à jour)
        DocumentEmbedding.objects.filter(
            content_type='idea',
            content_id=instance.id
        ).delete()
        
        # Créer le nouvel embedding
        vectorization_service.vectorize_idea(instance)
        
        action = "créée" if created else "modifiée"
        logger.info(f"Idée {instance.id} {action} et vectorisée automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la vectorisation automatique de l'idée {instance.id}: {e}")


@receiver(post_save, sender='accueil.Idea')
def send_idea_email_notification(sender, instance, created, **kwargs):
    """
    Envoyer un email automatique lors de la création d'une idée avec statut 'submitted'
    Les emails sont envoyés à tous les emails associés au département de l'idée
    """
    # Envoyer l'email seulement à la création et si le statut est 'submitted'
    if not created or instance.status != 'submitted':
        return
    
    try:
        # Récupérer les emails du département
        department = instance.department
        recipient_emails = department.get_emails_list()
        
        if not recipient_emails:
            logger.warning(f"Aucun email configuré pour le département {department.name} (idée {instance.id})")
            return
        
        # Préparer le contenu de l'email
        subject = f"Nouvelle idée pour {department.name} - Idée #{instance.id}"
        
        # Message en texte brut
        message_plain = f"""
Une nouvelle idée a été soumise pour le département {department.name}.

ID de l'idée: #{instance.id}
Département: {department.name}
Date de soumission: {instance.submitted_at.strftime('%d/%m/%Y à %H:%M')}

Description:
{instance.description}

---
Cet email a été envoyé automatiquement par le système de boîte à idées.
"""
        
        # Envoyer l'email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sar.sn')
        
        send_mail(
            subject=subject,
            message=message_plain,
            from_email=from_email,
            recipient_list=recipient_emails,
            fail_silently=False,  # Lever une exception si l'envoi échoue
        )
        
        logger.info(f"Email envoyé avec succès pour l'idée {instance.id} aux destinataires: {', '.join(recipient_emails)}")
        
    except Exception as e:
        # Logger l'erreur mais ne pas bloquer la sauvegarde de l'idée
        logger.error(f"Erreur lors de l'envoi de l'email pour l'idée {instance.id}: {e}", exc_info=True)


@receiver(post_delete, sender='accueil.Idea')
def remove_idea_embedding_on_delete(sender, instance, **kwargs):
    """
    Supprimer l'embedding d'une idée lors de sa suppression
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.models import DocumentEmbedding
        
        DocumentEmbedding.objects.filter(
            content_type='idea',
            content_id=instance.id
        ).delete()
        
        logger.info(f"Embedding de l'idée {instance.id} supprimé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'embedding de l'idée {instance.id}: {e}")


@receiver(post_save, sender='accueil.Event')
def vectorize_event_on_save(sender, instance, created, **kwargs):
    """
    Vectoriser automatiquement un événement lors de sa création ou modification
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.services.vectorization_service import VectorizationService
        from rag.models import DocumentEmbedding
        
        vectorization_service = VectorizationService()
        
        # Supprimer l'ancien embedding s'il existe (pour les mises à jour)
        DocumentEmbedding.objects.filter(
            content_type='event',
            content_id=instance.id
        ).delete()
        
        # Créer le nouvel embedding
        vectorization_service.vectorize_event(instance)
        
        action = "créé" if created else "modifié"
        logger.info(f"Événement {instance.id} {action} et vectorisé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la vectorisation automatique de l'événement {instance.id}: {e}")


@receiver(post_delete, sender='accueil.Event')
def remove_event_embedding_on_delete(sender, instance, **kwargs):
    """
    Supprimer l'embedding d'un événement lors de sa suppression
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.models import DocumentEmbedding
        
        DocumentEmbedding.objects.filter(
            content_type='event',
            content_id=instance.id
        ).delete()
        
        logger.info(f"Embedding de l'événement {instance.id} supprimé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'embedding de l'événement {instance.id}: {e}")


