import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Article

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def vectorize_article_on_save(sender, instance, created, **kwargs):
    """
    Vectoriser automatiquement un article lors de sa création ou modification
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.services.vectorization_service import VectorizationService
        from rag.models import DocumentEmbedding
        
        vectorization_service = VectorizationService()
        
        # Supprimer l'ancien embedding s'il existe (pour les mises à jour)
        DocumentEmbedding.objects.filter(
            content_type='article',
            content_id=instance.id
        ).delete()
        
        # Créer le nouvel embedding
        vectorization_service.vectorize_article(instance)
        
        action = "créé" if created else "modifié"
        logger.info(f"Article {instance.id} {action} et vectorisé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la vectorisation automatique de l'article {instance.id}: {e}")


@receiver(post_delete, sender=Article)
def remove_article_embedding_on_delete(sender, instance, **kwargs):
    """
    Supprimer l'embedding d'un article lors de sa suppression
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.models import DocumentEmbedding
        
        DocumentEmbedding.objects.filter(
            content_type='article',
            content_id=instance.id
        ).delete()
        
        logger.info(f"Embedding de l'article {instance.id} supprimé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'embedding de l'article {instance.id}: {e}")
