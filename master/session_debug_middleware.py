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
        is_forum_request = '/forum/' in request.path or '/api/forum/' in request.path
        
        if is_forum_request:
            print("=" * 80)
            print("🔧 [SESSION_MIDDLEWARE] === DÉBUT REQUÊTE FORUM ===")
            print(f"🔧 [SESSION_MIDDLEWARE] Path: {request.path}")
            print(f"🔧 [SESSION_MIDDLEWARE] Method: {request.method}")
            print(f"🔧 [SESSION_MIDDLEWARE] Full path: {request.get_full_path()}")
            print(f"🔧 [SESSION_MIDDLEWARE] Origin: {request.headers.get('Origin', 'N/A')}")
            print(f"🔧 [SESSION_MIDDLEWARE] Referer: {request.headers.get('Referer', 'N/A')}")
            print(f"🔧 [SESSION_MIDDLEWARE] User-Agent: {request.headers.get('User-Agent', 'N/A')[:100]}")
            print(f"🔧 [SESSION_MIDDLEWARE] Cookies reçus: {dict(request.COOKIES)}")
            print(f"🔧 [SESSION_MIDDLEWARE] Session key: {session_key}")
            print(f"🔧 [SESSION_MIDDLEWARE] Session existe: {request.session.exists(session_key) if session_key else False}")
            print(f"🔧 [SESSION_MIDDLEWARE] Authentifié: {request.user.is_authenticated if hasattr(request, 'user') else 'N/A'}")
            print(f"🔧 [SESSION_MIDDLEWARE] User: {request.user if hasattr(request, 'user') else 'N/A'}")
        
        response = self.get_response(request)
        
        # Log après le traitement de la requête (uniquement pour les requêtes forum)
        if is_forum_request:
            session_key_after = request.session.session_key
            print(f"🔧 [SESSION_MIDDLEWARE] === APRÈS TRAITEMENT FORUM ===")
            print(f"🔧 [SESSION_MIDDLEWARE] Status code: {response.status_code}")
            print(f"🔧 [SESSION_MIDDLEWARE] Content-Type: {response.get('Content-Type', 'N/A')}")
            print(f"🔧 [SESSION_MIDDLEWARE] Session key après: {session_key_after}")
            print(f"🔧 [SESSION_MIDDLEWARE] Session modifiée: {request.session.modified}")
            print(f"🔧 [SESSION_MIDDLEWARE] Cookies dans la réponse:")
            for cookie_name, cookie_obj in response.cookies.items():
                print(f"   - {cookie_name}: {cookie_obj.value[:50]}... (SameSite={cookie_obj.get('SameSite', 'N/A')}, Secure={cookie_obj.get('Secure', False)}, Domain={cookie_obj.get('Domain', 'N/A')})")
            print("=" * 80)
        
        return response






