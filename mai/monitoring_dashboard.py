"""
Dashboard de monitoring avancé pour la Phase 4.
Fournit des métriques en temps réel et des alertes intelligentes.
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import models
from django.core.cache import cache
from mai.models import RAGSearchLog, DocumentEmbedding
from mai.vector_search_service import vector_search_service
from mai.services import MAIService

logger = logging.getLogger(__name__)

class MonitoringDashboard:
    """Dashboard de monitoring avancé"""
    
    def __init__(self):
        self.mai_service = MAIService()
        self.vector_service = vector_search_service
        self.alert_thresholds = self._load_alert_thresholds()
        
    def _load_alert_thresholds(self) -> Dict[str, Any]:
        """Charge les seuils d'alerte"""
        return {
            'success_rate_min': 80.0,  # Taux de succès minimum
            'response_time_max': 2000.0,  # Temps de réponse maximum (ms)
            'error_rate_max': 10.0,  # Taux d'erreur maximum
            'concurrent_requests_max': 100,  # Requêtes simultanées maximum
            'memory_usage_max': 80.0,  # Utilisation mémoire maximum (%)
            'disk_usage_max': 90.0,  # Utilisation disque maximum (%)
            'vector_search_failure_rate_max': 15.0,  # Taux d'échec recherche vectorielle
            'heuristic_fallback_rate_max': 30.0  # Taux de fallback heuristique
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques en temps réel"""
        try:
            # Métriques de base
            base_metrics = self._get_base_metrics()
            
            # Métriques de performance
            performance_metrics = self._get_performance_metrics()
            
            # Métriques système
            system_metrics = self._get_system_metrics()
            
            # Métriques de qualité
            quality_metrics = self._get_quality_metrics()
            
            # Alertes
            alerts = self._generate_alerts(base_metrics, performance_metrics, system_metrics)
            
            return {
                'timestamp': timezone.now().isoformat(),
                'base_metrics': base_metrics,
                'performance_metrics': performance_metrics,
                'system_metrics': system_metrics,
                'quality_metrics': quality_metrics,
                'alerts': alerts,
                'status': self._determine_overall_status(alerts)
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques temps réel: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Récupère les métriques historiques"""
        try:
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Récupérer les logs
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            ).order_by('created_at')
            
            # Métriques par heure
            hourly_metrics = self._calculate_hourly_metrics(logs, start_time, end_time)
            
            # Métriques par méthode
            method_metrics = self._calculate_method_metrics(logs)
            
            # Tendances
            trends = self._calculate_trends(logs)
            
            # Top requêtes
            top_queries = self._get_top_queries(logs)
            
            return {
                'period_hours': hours,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'hourly_metrics': hourly_metrics,
                'method_metrics': method_metrics,
                'trends': trends,
                'top_queries': top_queries
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques historiques: {e}")
            return {'error': str(e)}
    
    def get_ab_test_results(self, test_id: Optional[str] = None) -> Dict[str, Any]:
        """Récupère les résultats des tests A/B"""
        try:
            # Récupérer les logs de test A/B
            ab_logs = RAGSearchLog.objects.filter(
                method__in=['vectorial', 'heuristic'],
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            # Analyser les performances par méthode
            vectorial_logs = ab_logs.filter(method='vectorial')
            heuristic_logs = ab_logs.filter(method='heuristic')
            
            vectorial_stats = self._calculate_method_stats(vectorial_logs)
            heuristic_stats = self._calculate_method_stats(heuristic_logs)
            
            # Comparaison
            comparison = self._compare_methods(vectorial_stats, heuristic_stats)
            
            # Recommandations
            recommendations = self._generate_ab_recommendations(comparison)
            
            return {
                'test_id': test_id or 'default',
                'vectorial_stats': vectorial_stats,
                'heuristic_stats': heuristic_stats,
                'comparison': comparison,
                'recommendations': recommendations,
                'winner': self._determine_winner(comparison)
            }
            
        except Exception as e:
            logger.error(f"Erreur résultats A/B: {e}")
            return {'error': str(e)}
    
    def get_health_check(self) -> Dict[str, Any]:
        """Vérification de santé du système"""
        try:
            health_checks = {}
            
            # Vérification base de données
            health_checks['database'] = self._check_database_health()
            
            # Vérification recherche vectorielle
            health_checks['vector_search'] = self._check_vector_search_health()
            
            # Vérification recherche heuristique
            health_checks['heuristic_search'] = self._check_heuristic_search_health()
            
            # Vérification cache
            health_checks['cache'] = self._check_cache_health()
            
            # Vérification mémoire
            health_checks['memory'] = self._check_memory_health()
            
            # Statut global
            overall_status = self._determine_health_status(health_checks)
            
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': overall_status,
                'checks': health_checks,
                'recommendations': self._generate_health_recommendations(health_checks)
            }
            
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return {
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _get_base_metrics(self) -> Dict[str, Any]:
        """Métriques de base"""
        try:
            # Dernière heure
            last_hour = timezone.now() - timedelta(hours=1)
            recent_logs = RAGSearchLog.objects.filter(created_at__gte=last_hour)
            
            total_searches = recent_logs.count()
            successful_searches = recent_logs.filter(success=True).count()
            failed_searches = recent_logs.filter(success=False).count()
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'failed_searches': failed_searches,
                'success_rate': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
                'error_rate': (failed_searches / total_searches * 100) if total_searches > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques de base: {e}")
            return {}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Métriques de performance"""
        try:
            # Dernière heure
            last_hour = timezone.now() - timedelta(hours=1)
            recent_logs = RAGSearchLog.objects.filter(created_at__gte=last_hour)
            
            # Temps de réponse
            response_times = recent_logs.values_list('response_time_ms', flat=True)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            
            # Métriques par méthode
            method_performance = {}
            for method in ['vectorial', 'heuristic', 'hybrid']:
                method_logs = recent_logs.filter(method=method)
                if method_logs.exists():
                    method_times = method_logs.values_list('response_time_ms', flat=True)
                    method_performance[method] = {
                        'count': method_logs.count(),
                        'avg_time': sum(method_times) / len(method_times) if method_times else 0,
                        'max_time': max(method_times) if method_times else 0,
                        'min_time': min(method_times) if method_times else 0
                    }
            
            return {
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'min_response_time_ms': min_response_time,
                'method_performance': method_performance
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques performance: {e}")
            return {}
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Métriques système"""
        try:
            import psutil
            
            # Utilisation CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Utilisation mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Utilisation disque
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free / (1024**3)  # GB
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': memory_available,
                'disk_percent': disk_percent,
                'disk_free_gb': disk_free
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques système: {e}")
            return {}
    
    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Métriques de qualité"""
        try:
            # Dernière heure
            last_hour = timezone.now() - timedelta(hours=1)
            recent_logs = RAGSearchLog.objects.filter(created_at__gte=last_hour)
            
            # Taux de fallback
            vectorial_logs = recent_logs.filter(method='vectorial')
            heuristic_logs = recent_logs.filter(method='heuristic')
            total_logs = recent_logs.count()
            
            vectorial_rate = (vectorial_logs.count() / total_logs * 100) if total_logs > 0 else 0
            heuristic_rate = (heuristic_logs.count() / total_logs * 100) if total_logs > 0 else 0
            
            # Qualité des résultats
            avg_results = recent_logs.aggregate(
                avg_results=models.Avg('results_count')
            )['avg_results'] or 0
            
            return {
                'vectorial_usage_rate': vectorial_rate,
                'heuristic_fallback_rate': heuristic_rate,
                'avg_results_per_search': avg_results,
                'quality_score': self._calculate_quality_score(recent_logs)
            }
            
        except Exception as e:
            logger.error(f"Erreur métriques qualité: {e}")
            return {}
    
    def _generate_alerts(self, base_metrics: Dict, performance_metrics: Dict, system_metrics: Dict) -> List[Dict[str, Any]]:
        """Génère des alertes basées sur les métriques"""
        alerts = []
        
        try:
            # Alerte taux de succès
            success_rate = base_metrics.get('success_rate', 0)
            if success_rate < self.alert_thresholds['success_rate_min']:
                alerts.append({
                    'type': 'warning',
                    'message': f'Taux de succès faible: {success_rate:.1f}%',
                    'threshold': self.alert_thresholds['success_rate_min'],
                    'current_value': success_rate
                })
            
            # Alerte temps de réponse
            avg_response_time = performance_metrics.get('avg_response_time_ms', 0)
            if avg_response_time > self.alert_thresholds['response_time_max']:
                alerts.append({
                    'type': 'warning',
                    'message': f'Temps de réponse élevé: {avg_response_time:.1f}ms',
                    'threshold': self.alert_thresholds['response_time_max'],
                    'current_value': avg_response_time
                })
            
            # Alerte mémoire
            memory_percent = system_metrics.get('memory_percent', 0)
            if memory_percent > self.alert_thresholds['memory_usage_max']:
                alerts.append({
                    'type': 'critical',
                    'message': f'Utilisation mémoire élevée: {memory_percent:.1f}%',
                    'threshold': self.alert_thresholds['memory_usage_max'],
                    'current_value': memory_percent
                })
            
            # Alerte disque
            disk_percent = system_metrics.get('disk_percent', 0)
            if disk_percent > self.alert_thresholds['disk_usage_max']:
                alerts.append({
                    'type': 'critical',
                    'message': f'Utilisation disque élevée: {disk_percent:.1f}%',
                    'threshold': self.alert_thresholds['disk_usage_max'],
                    'current_value': disk_percent
                })
            
        except Exception as e:
            logger.error(f"Erreur génération alertes: {e}")
            alerts.append({
                'type': 'error',
                'message': f'Erreur génération alertes: {e}'
            })
        
        return alerts
    
    def _determine_overall_status(self, alerts: List[Dict[str, Any]]) -> str:
        """Détermine le statut global du système"""
        if not alerts:
            return 'healthy'
        
        critical_alerts = [a for a in alerts if a.get('type') == 'critical']
        warning_alerts = [a for a in alerts if a.get('type') == 'warning']
        
        if critical_alerts:
            return 'critical'
        elif warning_alerts:
            return 'warning'
        else:
            return 'healthy'
    
    def _calculate_hourly_metrics(self, logs, start_time, end_time) -> List[Dict[str, Any]]:
        """Calcule les métriques par heure"""
        hourly_data = []
        
        try:
            current_time = start_time
            while current_time < end_time:
                next_hour = current_time + timedelta(hours=1)
                hour_logs = logs.filter(created_at__range=(current_time, next_hour))
                
                hourly_data.append({
                    'hour': current_time.strftime('%H:00'),
                    'total_searches': hour_logs.count(),
                    'successful_searches': hour_logs.filter(success=True).count(),
                    'avg_response_time': hour_logs.aggregate(
                        avg_time=models.Avg('response_time_ms')
                    )['avg_time'] or 0
                })
                
                current_time = next_hour
                
        except Exception as e:
            logger.error(f"Erreur calcul métriques horaires: {e}")
        
        return hourly_data
    
    def _calculate_method_metrics(self, logs) -> Dict[str, Any]:
        """Calcule les métriques par méthode"""
        try:
            method_stats = {}
            
            for method in ['vectorial', 'heuristic', 'hybrid']:
                method_logs = logs.filter(method=method)
                if method_logs.exists():
                    method_stats[method] = {
                        'count': method_logs.count(),
                        'success_rate': (method_logs.filter(success=True).count() / method_logs.count() * 100),
                        'avg_response_time': method_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0,
                        'avg_results': method_logs.aggregate(
                            avg_results=models.Avg('results_count')
                        )['avg_results'] or 0
                    }
            
            return method_stats
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques méthode: {e}")
            return {}
    
    def _calculate_trends(self, logs) -> Dict[str, Any]:
        """Calcule les tendances"""
        try:
            # Diviser en deux périodes
            total_logs = logs.count()
            mid_point = total_logs // 2
            
            first_half = logs[:mid_point]
            second_half = logs[mid_point:]
            
            # Comparer les performances
            first_half_success = first_half.filter(success=True).count()
            second_half_success = second_half.filter(success=True).count()
            
            first_half_rate = (first_half_success / first_half.count() * 100) if first_half.count() > 0 else 0
            second_half_rate = (second_half_success / second_half.count() * 100) if second_half.count() > 0 else 0
            
            return {
                'success_rate_trend': second_half_rate - first_half_rate,
                'performance_improving': second_half_rate > first_half_rate,
                'first_half_success_rate': first_half_rate,
                'second_half_success_rate': second_half_rate
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul tendances: {e}")
            return {}
    
    def _get_top_queries(self, logs, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les requêtes les plus fréquentes"""
        try:
            from django.db.models import Count
            
            query_counts = logs.values('query').annotate(
                count=Count('query')
            ).order_by('-count')[:limit]
            
            return [
                {
                    'query': item['query'],
                    'count': item['count']
                }
                for item in query_counts
            ]
            
        except Exception as e:
            logger.error(f"Erreur top requêtes: {e}")
            return []
    
    def _calculate_quality_score(self, logs) -> float:
        """Calcule un score de qualité global"""
        try:
            if not logs.exists():
                return 0.0
            
            # Facteurs de qualité
            success_rate = logs.filter(success=True).count() / logs.count()
            avg_results = logs.aggregate(
                avg_results=models.Avg('results_count')
            )['avg_results'] or 0
            
            # Score basé sur le taux de succès et le nombre de résultats
            quality_score = (success_rate * 0.7) + (min(avg_results / 3, 1.0) * 0.3)
            
            return quality_score * 100
            
        except Exception as e:
            logger.error(f"Erreur calcul score qualité: {e}")
            return 0.0
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Vérifie la santé de la base de données"""
        try:
            # Test de connexion
            DocumentEmbedding.objects.count()
            
            # Test de performance
            start_time = time.time()
            RAGSearchLog.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1)).count()
            query_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'connection_ok': True,
                'query_time_ms': query_time * 1000
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'connection_ok': False,
                'error': str(e)
            }
    
    def _check_vector_search_health(self) -> Dict[str, Any]:
        """Vérifie la santé de la recherche vectorielle"""
        try:
            # Test de recherche
            start_time = time.time()
            results = self.vector_service.search_similar("test", limit=1, threshold=0.1)
            search_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'search_ok': True,
                'search_time_ms': search_time * 1000,
                'results_count': len(results) if results else 0
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'search_ok': False,
                'error': str(e)
            }
    
    def _check_heuristic_search_health(self) -> Dict[str, Any]:
        """Vérifie la santé de la recherche heuristique"""
        try:
            # Test de recherche
            start_time = time.time()
            context = self.mai_service.get_context_for_question("test")
            search_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'search_ok': True,
                'search_time_ms': search_time * 1000,
                'context_length': len(context) if context else 0
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'search_ok': False,
                'error': str(e)
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Vérifie la santé du cache"""
        try:
            # Test de cache
            test_key = 'health_check_test'
            test_value = 'test_value'
            
            cache.set(test_key, test_value, timeout=60)
            retrieved_value = cache.get(test_key)
            
            return {
                'status': 'healthy' if retrieved_value == test_value else 'error',
                'cache_ok': retrieved_value == test_value
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'cache_ok': False,
                'error': str(e)
            }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Vérifie la santé de la mémoire"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            return {
                'status': 'healthy' if memory_percent < 90 else 'warning',
                'memory_percent': memory_percent,
                'available_gb': memory.available / (1024**3)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _determine_health_status(self, health_checks: Dict[str, Any]) -> str:
        """Détermine le statut global de santé"""
        statuses = [check.get('status', 'unknown') for check in health_checks.values()]
        
        if 'error' in statuses:
            return 'error'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'
    
    def _generate_health_recommendations(self, health_checks: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur les vérifications de santé"""
        recommendations = []
        
        for check_name, check_result in health_checks.items():
            status = check_result.get('status', 'unknown')
            
            if status == 'error':
                recommendations.append(f"Problème critique détecté dans {check_name}: {check_result.get('error', 'Erreur inconnue')}")
            elif status == 'warning':
                recommendations.append(f"Avertissement dans {check_name}: Vérification recommandée")
        
        return recommendations

# Instance globale
monitoring_dashboard = MonitoringDashboard()
