import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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


