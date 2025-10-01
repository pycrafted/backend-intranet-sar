"""
Middleware d'authentification personnalisé pour vérifier les sessions Django
"""
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

User = get_user_model()

class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware pour vérifier l'authentification sur les routes protégées
    """
    
    # Routes qui nécessitent une authentification
    PROTECTED_PATHS = [
        '/api/auth/current-user/',
        '/api/auth/check-auth/',
        '/api/auth/upload-avatar/',
        '/api/auth/change-password/',
    ]
    
    # Routes publiques (pas d'authentification requise)
    PUBLIC_PATHS = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/auth/csrf/',
        '/api/auth/logout/',  # Logout nécessite une session valide
    ]
    
    def process_request(self, request):
        """
        Vérifier l'authentification avant de traiter la requête
        """
        # Vérifier si la route nécessite une authentification
        if self._is_protected_path(request.path):
            # Vérifier si l'utilisateur est authentifié
            if not request.user.is_authenticated:
                # Debug: afficher les informations de session
                print(f"🔍 Middleware - Route: {request.path}")
                print(f"🔍 Middleware - User: {request.user}")
                print(f"🔍 Middleware - Authenticated: {request.user.is_authenticated}")
                print(f"🔍 Middleware - Session: {request.session}")
                print(f"🔍 Middleware - Cookies: {request.COOKIES}")
                
                return JsonResponse({
                    'error': 'Authentification requise',
                    'message': 'Vous devez être connecté pour accéder à cette ressource'
                }, status=401)
        
        return None
    
    def _is_protected_path(self, path):
        """
        Vérifier si le chemin nécessite une authentification
        """
        # Vérifier les chemins protégés
        for protected_path in self.PROTECTED_PATHS:
            if path.startswith(protected_path):
                return True
        
        # Vérifier que ce n'est pas un chemin public
        for public_path in self.PUBLIC_PATHS:
            if path.startswith(public_path):
                return False
        
        # Par défaut, considérer comme protégé
        return True
