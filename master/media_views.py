"""
Vues personnalisées pour servir les fichiers média avec les bons headers CORS
"""
import os
import mimetypes
import logging
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from corsheaders.decorators import cors_exempt

# Configuration du logger
logger = logging.getLogger(__name__)


@method_decorator(cors_exempt, name='dispatch')
class MediaView(View):
    """
    Vue pour servir les fichiers média avec les headers CORS appropriés
    """
    
    def get(self, request, path):
        # Log de débogage
        logger.info(f"🖼️ [MEDIA_VIEW] Requête fichier média: {path}")
        logger.info(f"🖼️ [MEDIA_VIEW] Origin: {request.META.get('HTTP_ORIGIN', 'Unknown')}")
        logger.info(f"🖼️ [MEDIA_VIEW] User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        
        # Construire le chemin complet vers le fichier
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        logger.info(f"🖼️ [MEDIA_VIEW] Chemin fichier: {file_path}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            logger.error(f"❌ [MEDIA_VIEW] Fichier non trouvé: {file_path}")
            raise Http404("Fichier non trouvé")
        
        # Vérifier que le chemin est sécurisé (pas de ..)
        if not os.path.abspath(file_path).startswith(settings.MEDIA_ROOT):
            raise Http404("Chemin non autorisé")
        
        # Déterminer le type MIME
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Lire le fichier
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            logger.info(f"✅ [MEDIA_VIEW] Fichier lu avec succès: {len(content)} bytes")
        except IOError as e:
            logger.error(f"❌ [MEDIA_VIEW] Erreur de lecture du fichier: {e}")
            raise Http404("Erreur de lecture du fichier")
        
        # Créer la réponse avec les headers CORS
        response = HttpResponse(content, content_type=content_type)
        logger.info(f"📤 [MEDIA_VIEW] Réponse créée avec content-type: {content_type}")
        
        # Headers CORS pour permettre l'accès depuis Vercel
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Max-Age'] = '86400'  # 24 heures
        
        # Headers de cache pour optimiser les performances
        response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
        response['ETag'] = f'"{os.path.getmtime(file_path)}"'
        
        return response
    
    def options(self, request, path):
        """Gérer les requêtes OPTIONS pour CORS"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Max-Age'] = '86400'
        return response
