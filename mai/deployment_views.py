"""
Vues API pour le déploiement et monitoring de la Phase 4.
Fournit des endpoints pour gérer le déploiement progressif et le monitoring.
"""
import json
import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from mai.deployment_manager import deployment_manager
from mai.monitoring_dashboard import monitoring_dashboard

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class DeploymentStatusView(View):
    """Vue pour le statut du déploiement"""
    
    def get(self, request):
        """Récupère le statut actuel du déploiement"""
        try:
            status = deployment_manager.get_deployment_status()
            return JsonResponse(status)
        except Exception as e:
            logger.error(f"Erreur statut déploiement: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeploymentControlView(View):
    """Vue pour contrôler le déploiement"""
    
    def post(self, request):
        """Démarre ou contrôle le déploiement"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'start':
                phase = data.get('phase', 'alpha')
                result = deployment_manager.start_deployment(phase)
                return JsonResponse(result)
            
            elif action == 'promote':
                result = deployment_manager.promote_to_next_phase()
                return JsonResponse(result)
            
            elif action == 'rollback':
                result = deployment_manager.rollback_deployment()
                return JsonResponse(result)
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Action invalide'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Erreur contrôle déploiement: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RealTimeMetricsView(View):
    """Vue pour les métriques en temps réel"""
    
    def get(self, request):
        """Récupère les métriques en temps réel"""
        try:
            metrics = monitoring_dashboard.get_real_time_metrics()
            return JsonResponse(metrics)
        except Exception as e:
            logger.error(f"Erreur métriques temps réel: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class HistoricalMetricsView(View):
    """Vue pour les métriques historiques"""
    
    def get(self, request):
        """Récupère les métriques historiques"""
        try:
            hours = int(request.GET.get('hours', 24))
            metrics = monitoring_dashboard.get_historical_metrics(hours)
            return JsonResponse(metrics)
        except Exception as e:
            logger.error(f"Erreur métriques historiques: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ABTestResultsView(View):
    """Vue pour les résultats des tests A/B"""
    
    def get(self, request):
        """Récupère les résultats des tests A/B"""
        try:
            test_id = request.GET.get('test_id')
            results = monitoring_dashboard.get_ab_test_results(test_id)
            return JsonResponse(results)
        except Exception as e:
            logger.error(f"Erreur résultats A/B: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """Vue pour la vérification de santé"""
    
    def get(self, request):
        """Effectue une vérification de santé complète"""
        try:
            health = monitoring_dashboard.get_health_check()
            return JsonResponse(health)
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return JsonResponse({
                'overall_status': 'error',
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeploymentRecommendationsView(View):
    """Vue pour les recommandations de déploiement"""
    
    def get(self, request):
        """Récupère les recommandations de déploiement"""
        try:
            recommendations = deployment_manager.get_deployment_recommendations()
            return JsonResponse({
                'recommendations': recommendations,
                'timestamp': monitoring_dashboard.get_real_time_metrics().get('timestamp')
            })
        except Exception as e:
            logger.error(f"Erreur recommandations: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SystemDashboardView(View):
    """Vue pour le dashboard système complet"""
    
    def get(self, request):
        """Récupère toutes les données du dashboard"""
        try:
            # Métriques en temps réel
            real_time_metrics = monitoring_dashboard.get_real_time_metrics()
            
            # Statut du déploiement
            deployment_status = deployment_manager.get_deployment_status()
            
            # Vérification de santé
            health_check = monitoring_dashboard.get_health_check()
            
            # Recommandations
            recommendations = deployment_manager.get_deployment_recommendations()
            
            return JsonResponse({
                'real_time_metrics': real_time_metrics,
                'deployment_status': deployment_status,
                'health_check': health_check,
                'recommendations': recommendations,
                'timestamp': real_time_metrics.get('timestamp')
            })
        except Exception as e:
            logger.error(f"Erreur dashboard système: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PerformanceOptimizationView(View):
    """Vue pour les optimisations de performance"""
    
    def get(self, request):
        """Récupère les suggestions d'optimisation"""
        try:
            # Analyser les performances
            metrics = monitoring_dashboard.get_real_time_metrics()
            performance_metrics = metrics.get('performance_metrics', {})
            base_metrics = metrics.get('base_metrics', {})
            
            optimizations = []
            
            # Optimisations basées sur le temps de réponse
            avg_response_time = performance_metrics.get('avg_response_time_ms', 0)
            if avg_response_time > 1000:
                optimizations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'title': 'Optimiser les temps de réponse',
                    'description': f'Temps de réponse moyen élevé: {avg_response_time:.1f}ms',
                    'suggestions': [
                        'Augmenter la taille du cache Redis',
                        'Optimiser les requêtes vectorielles',
                        'Implémenter la mise en cache des embeddings'
                    ]
                })
            
            # Optimisations basées sur le taux de succès
            success_rate = base_metrics.get('success_rate', 0)
            if success_rate < 90:
                optimizations.append({
                    'type': 'reliability',
                    'priority': 'high',
                    'title': 'Améliorer la fiabilité',
                    'description': f'Taux de succès faible: {success_rate:.1f}%',
                    'suggestions': [
                        'Ajuster les seuils de similarité',
                        'Améliorer la qualité des embeddings',
                        'Optimiser les requêtes de fallback'
                    ]
                })
            
            # Optimisations basées sur l'utilisation des méthodes
            method_performance = performance_metrics.get('method_performance', {})
            vectorial_perf = method_performance.get('vectorial', {})
            if vectorial_perf.get('count', 0) > 0:
                vectorial_avg_time = vectorial_perf.get('avg_time', 0)
                if vectorial_avg_time > 500:
                    optimizations.append({
                        'type': 'vector_search',
                        'priority': 'medium',
                        'title': 'Optimiser la recherche vectorielle',
                        'description': f'Temps de recherche vectorielle élevé: {vectorial_avg_time:.1f}ms',
                        'suggestions': [
                            'Optimiser l\'index vectoriel',
                            'Réduire la dimension des embeddings',
                            'Implémenter la recherche approximative'
                        ]
                    })
            
            return JsonResponse({
                'optimizations': optimizations,
                'total_optimizations': len(optimizations),
                'high_priority_count': len([o for o in optimizations if o['priority'] == 'high']),
                'timestamp': metrics.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Erreur optimisations: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AlertManagementView(View):
    """Vue pour la gestion des alertes"""
    
    def get(self, request):
        """Récupère les alertes actives"""
        try:
            metrics = monitoring_dashboard.get_real_time_metrics()
            alerts = metrics.get('alerts', [])
            
            # Catégoriser les alertes
            critical_alerts = [a for a in alerts if a.get('type') == 'critical']
            warning_alerts = [a for a in alerts if a.get('type') == 'warning']
            error_alerts = [a for a in alerts if a.get('type') == 'error']
            
            return JsonResponse({
                'alerts': alerts,
                'critical_count': len(critical_alerts),
                'warning_count': len(warning_alerts),
                'error_count': len(error_alerts),
                'total_alerts': len(alerts),
                'status': metrics.get('status', 'unknown')
            })
            
        except Exception as e:
            logger.error(f"Erreur gestion alertes: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)
    
    def post(self, request):
        """Acknowledge une alerte"""
        try:
            data = json.loads(request.body)
            alert_id = data.get('alert_id')
            action = data.get('action')
            
            if action == 'acknowledge':
                # Log l'acknowledgment
                logger.info(f"Alerte {alert_id} acknowledged")
                return JsonResponse({
                    'success': True,
                    'message': 'Alerte acknowledged'
                })
            elif action == 'dismiss':
                # Log le dismiss
                logger.info(f"Alerte {alert_id} dismissed")
                return JsonResponse({
                    'success': True,
                    'message': 'Alerte dismissed'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Action invalide'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Erreur gestion alerte: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)
