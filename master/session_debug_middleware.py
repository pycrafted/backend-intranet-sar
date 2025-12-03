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
        response = self.get_response(request)
        return response






