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

# Configuration du logger
logger = logging.getLogger(__name__)


class MediaView(View):
    """
    Vue pour servir les fichiers média avec les headers CORS appropriés
    """
    
    def get(self, request, path):
        # Log de débogage détaillé
        logger.info(f"🖼️ [MEDIA_VIEW] Requête fichier média: {path}")
        logger.info(f"🖼️ [MEDIA_VIEW] Origin: {request.META.get('HTTP_ORIGIN', 'Unknown')}")
        logger.info(f"🖼️ [MEDIA_VIEW] User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        logger.info(f"🖼️ [MEDIA_VIEW] Host: {request.META.get('HTTP_HOST', 'Unknown')}")
        logger.info(f"🖼️ [MEDIA_VIEW] Referer: {request.META.get('HTTP_REFERER', 'Unknown')}")
        logger.info(f"🖼️ [MEDIA_VIEW] Request method: {request.method}")
        logger.info(f"🖼️ [MEDIA_VIEW] Request headers: {dict(request.META)}")
        
        # Construire le chemin complet vers le fichier
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        logger.info(f"🖼️ [MEDIA_VIEW] Chemin fichier: {file_path}")
        logger.info(f"🖼️ [MEDIA_VIEW] MEDIA_ROOT: {settings.MEDIA_ROOT}")
        logger.info(f"🖼️ [MEDIA_VIEW] Chemin absolu: {os.path.abspath(file_path)}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            logger.error(f"❌ [MEDIA_VIEW] Fichier non trouvé: {file_path}")
            logger.error(f"❌ [MEDIA_VIEW] Liste des fichiers dans MEDIA_ROOT: {os.listdir(settings.MEDIA_ROOT) if os.path.exists(settings.MEDIA_ROOT) else 'MEDIA_ROOT n\'existe pas'}")
            logger.error(f"❌ [MEDIA_VIEW] Liste des fichiers dans articles: {os.listdir(os.path.join(settings.MEDIA_ROOT, 'articles')) if os.path.exists(os.path.join(settings.MEDIA_ROOT, 'articles')) else 'Dossier articles n\'existe pas'}")
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
        origin = request.META.get('HTTP_ORIGIN', '')
        logger.info(f"🌐 [MEDIA_VIEW] Origin reçu: {origin}")
        
        # Accepter toutes les origines Vercel et localhost
        if origin and (
            origin.endswith('.vercel.app') or 
            origin.startswith('https://frontend-intranet') or
            origin in ['http://localhost:3000', 'https://localhost:3000', 'http://127.0.0.1:3000']
        ):
            response['Access-Control-Allow-Origin'] = origin
            logger.info(f"✅ [MEDIA_VIEW] CORS autorisé pour: {origin}")
        else:
            response['Access-Control-Allow-Origin'] = '*'
            logger.info(f"🌍 [MEDIA_VIEW] CORS ouvert pour tous: {origin}")
            
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS, HEAD'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, Pragma'
        response['Access-Control-Allow-Credentials'] = 'false'  # Pas de cookies pour les images
        response['Access-Control-Max-Age'] = '86400'  # 24 heures
        response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Type, Cache-Control, ETag'
        
        # Headers de cache pour optimiser les performances
        response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
        response['ETag'] = f'"{os.path.getmtime(file_path)}"'
        
        return response
    
    def options(self, request, path):
        """Gérer les requêtes OPTIONS pour CORS"""
        logger.info(f"🔄 [MEDIA_VIEW] Requête OPTIONS pour: {path}")
        logger.info(f"🔄 [MEDIA_VIEW] Origin: {request.META.get('HTTP_ORIGIN', 'Unknown')}")
        
        response = HttpResponse()
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # Accepter toutes les origines Vercel et localhost
        if origin and (
            origin.endswith('.vercel.app') or 
            origin.startswith('https://frontend-intranet') or
            origin in ['http://localhost:3000', 'https://localhost:3000', 'http://127.0.0.1:3000']
        ):
            response['Access-Control-Allow-Origin'] = origin
            logger.info(f"✅ [MEDIA_VIEW] CORS OPTIONS autorisé pour: {origin}")
        else:
            response['Access-Control-Allow-Origin'] = '*'
            logger.info(f"🌍 [MEDIA_VIEW] CORS OPTIONS ouvert pour tous: {origin}")
            
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS, HEAD'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, Pragma'
        response['Access-Control-Allow-Credentials'] = 'false'
        response['Access-Control-Max-Age'] = '86400'
        response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Type, Cache-Control, ETag'
        return response
