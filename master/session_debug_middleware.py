"""
Middleware de débogage pour les sessions Django
"""
import logging

logger = logging.getLogger(__name__)

class SessionDebugMiddleware:
    """Middleware pour déboguer les problèmes de session"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log avant le traitement de la requête
        session_key = request.session.session_key
        print("=" * 80)
        print("🔧 [SESSION_MIDDLEWARE] === DÉBUT REQUÊTE ===")
        print(f"🔧 [SESSION_MIDDLEWARE] Path: {request.path}")
        print(f"🔧 [SESSION_MIDDLEWARE] Method: {request.method}")
        print(f"🔧 [SESSION_MIDDLEWARE] Origin: {request.headers.get('Origin', 'N/A')}")
        print(f"🔧 [SESSION_MIDDLEWARE] Cookies reçus: {dict(request.COOKIES)}")
        print(f"🔧 [SESSION_MIDDLEWARE] Session key: {session_key}")
        print(f"🔧 [SESSION_MIDDLEWARE] Session existe: {request.session.exists(session_key) if session_key else False}")
        print(f"🔧 [SESSION_MIDDLEWARE] Authentifié: {request.user.is_authenticated if hasattr(request, 'user') else 'N/A'}")
        
        response = self.get_response(request)
        
        # Log après le traitement de la requête
        session_key_after = request.session.session_key
        print(f"🔧 [SESSION_MIDDLEWARE] === APRÈS TRAITEMENT ===")
        print(f"🔧 [SESSION_MIDDLEWARE] Session key après: {session_key_after}")
        print(f"🔧 [SESSION_MIDDLEWARE] Session modifiée: {request.session.modified}")
        print(f"🔧 [SESSION_MIDDLEWARE] Cookies dans la réponse:")
        for cookie_name, cookie_obj in response.cookies.items():
            print(f"   - {cookie_name}: {cookie_obj.value[:50]}... (SameSite={cookie_obj.get('SameSite', 'N/A')}, Secure={cookie_obj.get('Secure', False)}, Domain={cookie_obj.get('Domain', 'N/A')})")
        print("=" * 80)
        
        return response






