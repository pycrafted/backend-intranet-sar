from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """
    Endpoint de santé pour le système
    """
    try:
        # Vérifier la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Vérifier le cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_status = "healthy" if cache.get('health_check') == 'ok' else "unhealthy"
    except Exception as e:
        cache_status = f"unhealthy: {str(e)}"
    
    # Statut global
    overall_status = "healthy" if db_status == "healthy" and cache_status == "healthy" else "unhealthy"
    
    return JsonResponse({
        "status": overall_status,
        "database": db_status,
        "cache": cache_status,
        "service": "sar_backend"
    })










