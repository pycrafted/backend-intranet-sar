"""
Middleware de performance pour mesurer le temps de chargement des pages
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection, reset_queries
from django.core.cache import cache

logger = logging.getLogger('performance')

class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour mesurer et logger les performances de chaque requête
    """
    
    def process_request(self, request):
        """Démarre le chronomètre et réinitialise les compteurs"""
        request._start_time = time.time()
        request._start_queries = len(connection.queries)
        reset_queries()
        
        # Ignorer les requêtes statiques et les favicon
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path == '/favicon.ico':
            return None
            
        return None
    
    def process_response(self, request, response):
        """Calcule et log les métriques de performance"""
        # Ignorer les requêtes statiques
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path == '/favicon.ico':
            return response
        
        if not hasattr(request, '_start_time'):
            return response
        
        # Calculer le temps total
        total_time = time.time() - request._start_time
        
        # Compter les requêtes SQL
        num_queries = len(connection.queries) - request._start_queries
        
        # Calculer le temps total des requêtes SQL
        sql_time = sum(float(q['time']) for q in connection.queries[request._start_queries:])
        
        # Temps de traitement (hors SQL)
        processing_time = total_time - sql_time
        
        # Déterminer le niveau de log selon la performance
        if total_time > 2.0:
            log_level = 'error'
            emoji = '🔴'
        elif total_time > 1.0:
            log_level = 'warning'
            emoji = '🟡'
        elif total_time > 0.5:
            log_level = 'info'
            emoji = '🟠'
        else:
            log_level = 'info'
            emoji = '🟢'
        
        # Préparer le message de log
        log_message = (
            f"{emoji} [PERF] {request.method} {request.path} | "
            f"Temps total: {total_time*1000:.2f}ms | "
            f"SQL: {num_queries} requêtes ({sql_time*1000:.2f}ms) | "
            f"Traitement: {processing_time*1000:.2f}ms | "
            f"Status: {response.status_code}"
        )
        
        # Log détaillé pour les requêtes lentes
        if total_time > 0.5:
            log_message += f" | User: {request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonyme'}"
            
            # Détails des requêtes SQL si trop nombreuses
            if num_queries > 10:
                log_message += f"\n   ⚠️  Trop de requêtes SQL ({num_queries}) - Optimisation nécessaire"
                # Logger les premières requêtes pour analyse
                for i, query in enumerate(connection.queries[request._start_queries:request._start_queries+5]):
                    log_message += f"\n   SQL[{i+1}]: {query['sql'][:100]}... ({query['time']}s)"
        
        # Logger selon le niveau
        if log_level == 'error':
            logger.error(log_message)
        elif log_level == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Ajouter les métriques dans les headers de réponse (pour debug)
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
            response['X-Performance-Total'] = f"{total_time*1000:.2f}ms"
            response['X-Performance-SQL'] = f"{num_queries} queries, {sql_time*1000:.2f}ms"
            response['X-Performance-Processing'] = f"{processing_time*1000:.2f}ms"
        
        return response










