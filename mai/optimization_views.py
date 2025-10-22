"""
Vues d'optimisation pour la Phase 6.
Expose les fonctionnalités d'optimisation via l'API REST.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from mai.optimization_service import intelligent_optimization_service
from mai.cache_service import cache_service as advanced_cache_service
from mai.vector_index_service import vector_index_service
from mai.monitoring_service import advanced_monitoring_service

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([])
def run_comprehensive_optimization(request):
    """
    Exécute une optimisation complète du système RAG.
    """
    try:
        logger.info("🚀 Démarrage optimisation complète via API")
        
        # Exécuter l'optimisation complète
        result = intelligent_optimization_service.run_comprehensive_optimization()
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Optimisation complète terminée avec succès',
                'duration_seconds': result['duration_seconds'],
                'results': result['optimization_results']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Erreur inconnue'),
                'duration_seconds': result.get('duration_seconds', 0)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Erreur optimisation complète API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_optimization_status(request):
    """
    Retourne le statut actuel de l'optimisation du système.
    """
    try:
        status_data = intelligent_optimization_service.get_optimization_status()
        
        return Response({
            'success': True,
            'status': status_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur statut optimisation API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([])
def optimize_cache(request):
    """
    Optimise spécifiquement le cache Redis.
    """
    try:
        logger.info("📦 Optimisation cache via API")
        
        # Optimiser le cache
        cache_health = advanced_cache_service.get_cache_health()
        optimization_result = advanced_cache_service.optimize_cache()
        warmup_result = advanced_cache_service.warm_up_cache()
        final_stats = advanced_cache_service.get_cache_stats()
        
        return Response({
            'success': True,
            'message': 'Optimisation du cache terminée',
            'health_before': cache_health,
            'optimization': optimization_result,
            'warmup': warmup_result,
            'final_stats': final_stats
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur optimisation cache API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([])
def optimize_vector_indexes(request):
    """
    Optimise spécifiquement les index vectoriels.
    """
    try:
        logger.info("🔍 Optimisation index vectoriels via API")
        
        # Analyser les performances
        performance_analysis = vector_index_service.analyze_index_performance()
        
        # Vérifier si reindexation nécessaire
        reindex_result = vector_index_service.reindex_if_needed()
        
        # Optimiser l'index
        optimization_result = vector_index_service.optimize_existing_index()
        
        # Vérifier la santé
        health_check = vector_index_service.get_index_health()
        
        return Response({
            'success': True,
            'message': 'Optimisation des index terminée',
            'performance_analysis': performance_analysis,
            'reindex_check': reindex_result,
            'optimization': optimization_result,
            'health_check': health_check
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur optimisation index API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_cache_stats(request):
    """
    Retourne les statistiques détaillées du cache Redis.
    """
    try:
        cache_stats = advanced_cache_service.get_cache_stats()
        cache_health = advanced_cache_service.get_cache_health()
        
        return Response({
            'success': True,
            'stats': cache_stats,
            'health': cache_health
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur stats cache API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_index_performance(request):
    """
    Retourne l'analyse de performance des index vectoriels.
    """
    try:
        performance_analysis = vector_index_service.analyze_index_performance()
        index_health = vector_index_service.get_index_health()
        
        return Response({
            'success': True,
            'performance': performance_analysis,
            'health': index_health
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur performance index API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_system_health(request):
    """
    Retourne la santé globale du système.
    """
    try:
        # Collecter les métriques système
        system_metrics = advanced_monitoring_service.collect_system_metrics()
        
        # Vérifier la santé du système
        health_check = advanced_monitoring_service.check_system_health()
        
        # Obtenir le rapport de performance
        performance_report = advanced_monitoring_service.get_performance_report(hours=24)
        
        # Obtenir le résumé des alertes
        alerts_summary = advanced_monitoring_service.get_alerts_summary()
        
        return Response({
            'success': True,
            'system_metrics': system_metrics,
            'health_check': health_check,
            'performance_report': performance_report,
            'alerts_summary': alerts_summary
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur santé système API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([])
def schedule_automatic_optimization(request):
    """
    Planifie une optimisation automatique.
    """
    try:
        result = intelligent_optimization_service.schedule_automatic_optimization()
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'Optimisation automatique planifiée',
                'scheduled_time': result['scheduled_time'],
                'interval_hours': result['interval_hours']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Erreur planification optimisation API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([])
def clear_cache(request):
    """
    Vide le cache Redis.
    """
    try:
        pattern = request.data.get('pattern', None)
        
        result = advanced_cache_service.clear_cache(pattern)
        
        if result:
            return Response({
                'success': True,
                'message': 'Cache vidé avec succès',
                'pattern': pattern
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Erreur lors du vidage du cache'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Erreur clear cache API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_optimization_history(request):
    """
    Retourne l'historique des optimisations.
    """
    try:
        history = intelligent_optimization_service.performance_history
        
        return Response({
            'success': True,
            'history': history[-50:],  # 50 dernières optimisations
            'total_count': len(history)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Erreur historique optimisation API: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
