"""
Vues API pour la Phase 6 - Optimisations Avancées.
Expose les fonctionnalités de cache, d'optimisation d'index et de monitoring.
"""
import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from mai.cache_service import cache_service as advanced_cache_service
from mai.vector_index_service import vector_index_service
from mai.monitoring_service import advanced_monitoring_service

logger = logging.getLogger(__name__)

# ============================================================================
# CACHE MANAGEMENT VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def cache_status(request):
    """Statut du cache local (Redis désactivé)"""
    try:
        stats = advanced_cache_service.get_cache_stats()
        health = advanced_cache_service.health_check()
        
        return Response({
            'success': True,
            'cache_stats': stats,
            'cache_health': health,
            'redis_disabled': True,
            'message': 'Redis complètement désactivé - Cache local uniquement',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur cache status: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'redis_disabled': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def cache_optimize(request):
    """Optimise le cache local (Redis désactivé)"""
    try:
        result = advanced_cache_service.optimize_cache()
        
        return Response({
            'success': result['success'],
            'message': result['message'],
            'stats': result.get('stats', {}),
            'redis_disabled': True,
            'message_redis': 'Redis complètement désactivé - Cache local uniquement',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur cache optimize: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'redis_disabled': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def cache_warm_up(request):
    """Préchauffe le cache avec des données fréquentes"""
    try:
        result = advanced_cache_service.warm_up_cache()
        
        return Response({
            'success': result['success'],
            'message': result['message'],
            'warmed_items': result.get('warmed_items', 0),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur cache warm-up: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def cache_clear(request):
    """Vide le cache Redis"""
    try:
        pattern = request.data.get('pattern', None)
        result = advanced_cache_service.clear_cache(pattern)
        
        return Response({
            'success': result,
            'message': f'Cache vidé{" avec pattern" if pattern else ""}',
            'pattern': pattern,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur cache clear: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# VECTOR INDEX OPTIMIZATION VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def index_status(request):
    """Statut des index vectoriels"""
    try:
        health = vector_index_service.get_index_health()
        performance = vector_index_service.analyze_index_performance()
        
        return Response({
            'success': True,
            'index_health': health,
            'index_performance': performance,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur index status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def index_build(request):
    """Construit un nouvel index vectoriel optimisé"""
    try:
        index_type = request.data.get('index_type', 'ivfflat')
        result = vector_index_service.build_optimized_index(index_type)
        
        return Response({
            'success': result['success'],
            'message': result.get('message', 'Index construit'),
            'index_type': result.get('index_type', index_type),
            'duration_seconds': result.get('duration_seconds', 0),
            'index_size': result.get('index_size', 'N/A'),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur index build: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def index_optimize(request):
    """Optimise l'index existant"""
    try:
        result = vector_index_service.optimize_existing_index()
        
        return Response({
            'success': result['success'],
            'message': result.get('message', 'Index optimisé'),
            'duration_seconds': result.get('duration_seconds', 0),
            'index_stats': result.get('index_stats', {}),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur index optimize: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def index_reindex_if_needed(request):
    """Reindexe si nécessaire"""
    try:
        result = vector_index_service.reindex_if_needed()
        
        return Response({
            'success': result['success'],
            'message': result.get('message', 'Vérification reindexation'),
            'new_documents': result.get('new_documents', 0),
            'threshold': result.get('threshold', 0),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur reindex check: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def index_history(request):
    """Historique des optimisations d'index"""
    try:
        history = vector_index_service.get_optimization_history()
        
        return Response({
            'success': True,
            'optimization_history': history,
            'total_optimizations': len(history),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur index history: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# MONITORING VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_metrics(request):
    """Métriques système en temps réel"""
    try:
        metrics = advanced_monitoring_service.collect_system_metrics()
        
        return Response({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur monitoring metrics: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_health(request):
    """Vérification de la santé du système"""
    try:
        health = advanced_monitoring_service.check_system_health()
        
        return Response({
            'success': True,
            'health': health,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur monitoring health: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_report(request):
    """Rapport de performance"""
    try:
        hours = int(request.GET.get('hours', 24))
        report = advanced_monitoring_service.get_performance_report(hours)
        
        return Response({
            'success': report['success'],
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur monitoring report: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_alerts(request):
    """Résumé des alertes"""
    try:
        alerts_summary = advanced_monitoring_service.get_alerts_summary()
        
        return Response({
            'success': True,
            'alerts': alerts_summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur monitoring alerts: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def monitoring_acknowledge_alert(request):
    """Acquitte une alerte"""
    try:
        alert_index = request.data.get('alert_index')
        if alert_index is None:
            return Response({
                'success': False,
                'error': 'alert_index requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = advanced_monitoring_service.acknowledge_alert(alert_index)
        
        return Response({
            'success': result,
            'message': 'Alerte acquittée' if result else 'Erreur acquittement',
            'alert_index': alert_index,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur acknowledge alert: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def monitoring_cleanup(request):
    """Nettoie les anciennes données de monitoring"""
    try:
        days = int(request.data.get('days', 30))
        result = advanced_monitoring_service.clear_old_data(days)
        
        return Response({
            'success': result['success'],
            'message': 'Données nettoyées' if result['success'] else 'Erreur nettoyage',
            'cleaned_metrics': result.get('cleaned_metrics', 0),
            'cleaned_alerts': result.get('cleaned_alerts', 0),
            'remaining_metrics': result.get('remaining_metrics', 0),
            'remaining_alerts': result.get('remaining_alerts', 0),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur monitoring cleanup: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# PHASE 6 DASHBOARD VIEW
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def phase6_dashboard(request):
    """Dashboard complet de la Phase 6"""
    try:
        # Collecter toutes les métriques
        cache_stats = advanced_cache_service.get_cache_stats()
        cache_health = advanced_cache_service.get_cache_health()
        
        index_health = vector_index_service.get_index_health()
        index_performance = vector_index_service.analyze_index_performance()
        
        system_metrics = advanced_monitoring_service.collect_system_metrics()
        system_health = advanced_monitoring_service.check_system_health()
        alerts_summary = advanced_monitoring_service.get_alerts_summary()
        
        # Générer le rapport de performance
        performance_report = advanced_monitoring_service.get_performance_report(24)
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'cache': {
                'stats': cache_stats,
                'health': cache_health
            },
            'index': {
                'health': index_health,
                'performance': index_performance
            },
            'monitoring': {
                'metrics': system_metrics,
                'health': system_health,
                'alerts': alerts_summary,
                'performance_report': performance_report
            },
            'overall_status': {
                'cache_status': cache_health.get('status', 'unknown'),
                'index_status': index_health.get('status', 'unknown'),
                'system_status': system_health.get('status', 'unknown'),
                'total_alerts': alerts_summary.get('total_alerts', 0),
                'critical_alerts': alerts_summary.get('critical_alerts', 0)
            }
        }
        
        return Response({
            'success': True,
            'dashboard': dashboard_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur phase6 dashboard: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# OPTIMIZATION RECOMMENDATIONS VIEW
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def optimization_recommendations(request):
    """Recommandations d'optimisation basées sur l'analyse"""
    try:
        recommendations = []
        
        # Analyser le cache
        cache_health = advanced_cache_service.get_cache_health()
        if cache_health.get('status') == 'unhealthy':
            recommendations.append({
                'category': 'cache',
                'priority': 'high',
                'title': 'Problème de cache Redis',
                'description': cache_health.get('reason', 'Cache non disponible'),
                'recommendations': cache_health.get('recommendations', [])
            })
        
        # Analyser l'index
        index_health = vector_index_service.get_index_health()
        if index_health.get('status') in ['missing', 'fragmented', 'unused']:
            recommendations.append({
                'category': 'index',
                'priority': 'high' if index_health.get('status') == 'missing' else 'medium',
                'title': f"Problème d'index: {index_health.get('status')}",
                'description': index_health.get('message', 'Index vectoriel problématique'),
                'recommendations': index_health.get('recommendations', [])
            })
        
        # Analyser le système
        system_health = advanced_monitoring_service.check_system_health()
        if system_health.get('status') in ['warning', 'critical']:
            recommendations.append({
                'category': 'system',
                'priority': 'high' if system_health.get('status') == 'critical' else 'medium',
                'title': f"Problème système: {system_health.get('status')}",
                'description': f"Score de santé: {system_health.get('health_score', 0)}",
                'recommendations': system_health.get('recommendations', [])
            })
        
        # Analyser les performances
        performance_report = advanced_monitoring_service.get_performance_report(24)
        if performance_report.get('success'):
            perf_stats = performance_report.get('performance_stats', {})
            if perf_stats.get('avg_response_time_ms', 0) > 500:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': 'Temps de réponse élevé',
                    'description': f"Temps moyen: {perf_stats.get('avg_response_time_ms', 0)}ms",
                    'recommendations': ['Optimiser les requêtes', 'Améliorer le cache', 'Optimiser les index']
                })
        
        # Calculer le score global
        total_recommendations = len(recommendations)
        high_priority = len([r for r in recommendations if r['priority'] == 'high'])
        medium_priority = len([r for r in recommendations if r['priority'] == 'medium'])
        
        overall_score = 100
        if high_priority > 0:
            overall_score -= high_priority * 30
        if medium_priority > 0:
            overall_score -= medium_priority * 15
        
        overall_score = max(0, overall_score)
        
        return Response({
            'success': True,
            'recommendations': recommendations,
            'summary': {
                'total_recommendations': total_recommendations,
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'overall_score': overall_score
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur optimization recommendations: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
