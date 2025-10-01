import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='annuaire.Employee')
def vectorize_employee_on_save(sender, instance, created, **kwargs):
    """
    Vectoriser automatiquement un employé lors de sa création ou modification
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.services.vectorization_service import VectorizationService
        from rag.models import DocumentEmbedding
        
        vectorization_service = VectorizationService()
        
        # Supprimer l'ancien embedding s'il existe (pour les mises à jour)
        DocumentEmbedding.objects.filter(
            content_type='employee',
            content_id=instance.id
        ).delete()
        
        # Créer le nouvel embedding
        vectorization_service.vectorize_employee(instance)
        
        action = "créé" if created else "modifié"
        logger.info(f"Employé {instance.id} {action} et vectorisé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la vectorisation automatique de l'employé {instance.id}: {e}")


@receiver(post_save, sender='annuaire.Employee')
def update_hierarchy_levels_on_save(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement les niveaux hiérarchiques quand un employé change de manager
    """
    try:
        # Mettre à jour les niveaux de tous les subordonnés de cet employé
        instance.update_hierarchy_levels()
        
        action = "créé" if created else "modifié"
        logger.info(f"Niveaux hiérarchiques mis à jour pour l'employé {instance.id} ({action})")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des niveaux hiérarchiques pour l'employé {instance.id}: {e}")


@receiver(post_delete, sender='annuaire.Employee')
def remove_employee_embedding_on_delete(sender, instance, **kwargs):
    """
    Supprimer l'embedding d'un employé lors de sa suppression
    """
    try:
        # Import conditionnel pour éviter les dépendances circulaires
        from rag.models import DocumentEmbedding
        
        DocumentEmbedding.objects.filter(
            content_type='employee',
            content_id=instance.id
        ).delete()
        
        logger.info(f"Embedding de l'employé {instance.id} supprimé automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'embedding de l'employé {instance.id}: {e}")
