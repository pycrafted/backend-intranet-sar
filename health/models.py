from django.db import models

# L'app health n'a pas besoin de modèles complexes
# Elle sert uniquement pour les endpoints de santé de l'API

class HealthCheck(models.Model):
    """
    Modèle simple pour tracker les health checks
    (optionnel - peut être vide)
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='healthy')
    
    class Meta:
        ordering = ['-timestamp']
