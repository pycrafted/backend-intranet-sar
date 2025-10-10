"""
Vues CORS personnalisées pour les endpoints documents
Ces vues n'ont pas besoin d'authentification et utilisent des headers CORS simplifiés
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from corsheaders.decorators import cors_exempt
import json

@method_decorator(cors_exempt, name='dispatch')
class DocumentsCORSView(View):
    """
    Vue de base pour les endpoints documents avec CORS simplifié
    """
    
    def options(self, request, *args, **kwargs):
        """Gérer les requêtes OPTIONS (preflight) pour CORS"""
        response = JsonResponse({})
        
        # Headers CORS pour les documents (sans credentials)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-CSRFToken'
        response['Access-Control-Max-Age'] = '86400'  # Cache preflight pour 24h
        
        return response
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch pour ajouter les headers CORS à toutes les réponses"""
        response = super().dispatch(request, *args, **kwargs)
        
        # Ajouter les headers CORS à toutes les réponses
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-CSRFToken'
        
        return response
