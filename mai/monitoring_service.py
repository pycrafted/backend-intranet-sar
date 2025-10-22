"""
Service de monitoring avancé pour la Phase 6.
Surveille les performances, la santé du système et génère des alertes.
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db import connection
from django.utils import timezone
from django.core.cache import cache
from mai.models import RAGSearchLog, DocumentEmbedding
from django.db import models
from mai.cache_service import cache_service as advanced_cache_service
from mai.vector_index_service import vector_index_service

logger = logging.getLogger(__name__)

class AdvancedMonitoringService:
    """Service de monitoring avancé avec alertes intelligentes"""
    
    def __init__(self):
        self.monitoring_config = self._load_monitoring_config()
        self.metrics_history = []
        self.alerts_history = []
        
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Charge la configuration du monitoring"""
        return {
            'thresholds': {
                'response_time_ms': 1000,
                'success_rate_percent': 95,
                'memory_usage_percent': 80,
                'cpu_usage_percent': 80,
                'disk_usage_percent': 90,
                'cache_hit_rate_percent': 70,
                'error_rate_percent': 5
            },
            'intervals': {
                'metrics_collection_minutes': 5,
                'health_check_minutes': 10,
                'alert_check_minutes': 2,
                'report_generation_hours': 1
            },
            'alerts': {
                'enabled': True,
                'email_notifications': False,
                'webhook_url': None,
                'retention_days': 30
            },
            'performance': {
                'target_queries_per_second': 10,
                'target_response_time_ms': 500,
                'target_availability_percent': 99.9
            }
        }
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques système en temps réel"""
        try:
            # Métriques système
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métriques Django
            db_connections = len(connection.queries) if hasattr(connection, 'queries') else 0
            
            # Métriques RAG
            total_searches = RAGSearchLog.objects.count()
            recent_searches = RAGSearchLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            # Métriques de performance récentes
            recent_logs = RAGSearchLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(minutes=5)
            )
            
            if recent_logs.exists():
                avg_response_time = recent_logs.aggregate(
                    avg_time=models.Avg('response_time_ms')
                )['avg_time'] or 0
                
                success_rate = (recent_logs.filter(success=True).count() / recent_logs.count()) * 100
            else:
                avg_response_time = 0
                success_rate = 100
            
            # Métriques de cache
            cache_stats = advanced_cache_service.get_cache_stats()
            
            # Métriques de base de données
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM rag_documentembedding")
                total_embeddings = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size('rag_documentembedding')) as table_size
                """)
                table_size = cursor.fetchone()[0]
            
            metrics = {
                'timestamp': timezone.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': round(memory.used / 1024 / 1024, 2),
                    'memory_available_mb': round(memory.available / 1024 / 1024, 2),
                    'disk_percent': disk.percent,
                    'disk_used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
                },
                'database': {
                    'total_embeddings': total_embeddings,
                    'table_size': table_size,
                    'active_connections': db_connections
                },
                'rag': {
                    'total_searches': total_searches,
                    'recent_searches_1h': recent_searches,
                    'avg_response_time_ms': round(avg_response_time, 2),
                    'success_rate_percent': round(success_rate, 2)
                },
                'cache': cache_stats,
                'performance': {
                    'queries_per_second': round(recent_searches / 3600, 2),
                    'response_time_trend': self._calculate_response_time_trend(),
                    'success_rate_trend': self._calculate_success_rate_trend()
                }
            }
            
            # Stocker les métriques
            self.metrics_history.append(metrics)
            
            # Garder seulement les 1000 dernières entrées
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques: {e}")
            return {
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }
    
    def _calculate_response_time_trend(self) -> str:
        """Calcule la tendance du temps de réponse"""
        try:
            if len(self.metrics_history) < 2:
                return 'stable'
            
            recent = self.metrics_history[-1]['rag']['avg_response_time_ms']
            previous = self.metrics_history[-2]['rag']['avg_response_time_ms']
            
            if recent > previous * 1.2:
                return 'increasing'
            elif recent < previous * 0.8:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception:
            return 'unknown'
    
    def _calculate_success_rate_trend(self) -> str:
        """Calcule la tendance du taux de succès"""
        try:
            if len(self.metrics_history) < 2:
                return 'stable'
            
            recent = self.metrics_history[-1]['rag']['success_rate_percent']
            previous = self.metrics_history[-2]['rag']['success_rate_percent']
            
            if recent < previous - 5:
                return 'decreasing'
            elif recent > previous + 5:
                return 'increasing'
            else:
                return 'stable'
                
        except Exception:
            return 'unknown'
    
    def check_system_health(self) -> Dict[str, Any]:
        """Vérifie la santé globale du système"""
        try:
            metrics = self.collect_system_metrics()
            
            health_issues = []
            health_score = 100
            
            # Vérifier les seuils
            thresholds = self.monitoring_config['thresholds']
            
            # CPU
            if metrics['system']['cpu_percent'] > thresholds['cpu_usage_percent']:
                health_issues.append(f"CPU élevé: {metrics['system']['cpu_percent']}%")
                health_score -= 20
            
            # Mémoire
            if metrics['system']['memory_percent'] > thresholds['memory_usage_percent']:
                health_issues.append(f"Mémoire élevée: {metrics['system']['memory_percent']}%")
                health_score -= 20
            
            # Disque
            if metrics['system']['disk_percent'] > thresholds['disk_usage_percent']:
                health_issues.append(f"Disque plein: {metrics['system']['disk_percent']}%")
                health_score -= 15
            
            # Temps de réponse
            if metrics['rag']['avg_response_time_ms'] > thresholds['response_time_ms']:
                health_issues.append(f"Temps de réponse élevé: {metrics['rag']['avg_response_time_ms']}ms")
                health_score -= 25
            
            # Taux de succès
            if metrics['rag']['success_rate_percent'] < thresholds['success_rate_percent']:
                health_issues.append(f"Taux de succès faible: {metrics['rag']['success_rate_percent']}%")
                health_score -= 30
            
            # Cache hit rate
            if metrics['cache']['status'] == 'active':
                hit_rate = metrics['cache']['hit_rate']
                if hit_rate < thresholds['cache_hit_rate_percent']:
                    health_issues.append(f"Cache hit rate faible: {hit_rate}%")
                    health_score -= 10
            
            # Déterminer le statut de santé
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 70:
                status = 'good'
            elif health_score >= 50:
                status = 'warning'
            else:
                status = 'critical'
            
            # Générer des recommandations
            recommendations = self._generate_health_recommendations(health_issues, metrics)
            
            health_data = {
                'timestamp': timezone.now().isoformat(),
                'status': status,
                'health_score': max(0, health_score),
                'issues': health_issues,
                'recommendations': recommendations,
                'metrics': metrics
            }
            
            # Enregistrer l'alerte si nécessaire
            if status in ['warning', 'critical']:
                self._create_alert(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return {
                'timestamp': timezone.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'health_score': 0
            }
    
    def _generate_health_recommendations(self, issues: List[str], metrics: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur les problèmes détectés"""
        recommendations = []
        
        for issue in issues:
            if 'CPU élevé' in issue:
                recommendations.append("Considérer l'optimisation des requêtes ou l'ajout de ressources CPU")
            elif 'Mémoire élevée' in issue:
                recommendations.append("Optimiser l'utilisation mémoire ou augmenter la RAM")
            elif 'Disque plein' in issue:
                recommendations.append("Nettoyer les fichiers temporaires ou augmenter l'espace disque")
            elif 'Temps de réponse élevé' in issue:
                recommendations.append("Optimiser les index vectoriels ou le cache")
            elif 'Taux de succès faible' in issue:
                recommendations.append("Vérifier les logs d'erreur et la configuration")
            elif 'Cache hit rate faible' in issue:
                recommendations.append("Optimiser la stratégie de cache ou augmenter la taille du cache")
        
        if not recommendations:
            recommendations.append("Système en bonne santé - continuer la surveillance")
        
        return recommendations
    
    def _create_alert(self, health_data: Dict[str, Any]) -> None:
        """Crée une alerte basée sur les données de santé"""
        try:
            alert = {
                'timestamp': timezone.now().isoformat(),
                'level': health_data['status'],
                'message': f"Santé système: {health_data['status']}",
                'health_score': health_data['health_score'],
                'issues': health_data['issues'],
                'recommendations': health_data['recommendations'],
                'acknowledged': False
            }
            
            self.alerts_history.append(alert)
            
            # Garder seulement les 500 dernières alertes
            if len(self.alerts_history) > 500:
                self.alerts_history = self.alerts_history[-500:]
            
            logger.warning(f"Alerte système: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Erreur création alerte: {e}")
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Génère un rapport de performance"""
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            # Filtrer les métriques récentes
            recent_metrics = [
                m for m in self.metrics_history
                if timezone.datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    'success': False,
                    'message': 'Aucune donnée disponible pour la période'
                }
            
            # Calculer les statistiques
            response_times = [m['rag']['avg_response_time_ms'] for m in recent_metrics if 'rag' in m]
            success_rates = [m['rag']['success_rate_percent'] for m in recent_metrics if 'rag' in m]
            cpu_usage = [m['system']['cpu_percent'] for m in recent_metrics if 'system' in m]
            memory_usage = [m['system']['memory_percent'] for m in recent_metrics if 'system' in m]
            
            # Statistiques de performance
            performance_stats = {
                'avg_response_time_ms': round(sum(response_times) / len(response_times), 2) if response_times else 0,
                'min_response_time_ms': min(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0,
                'avg_success_rate_percent': round(sum(success_rates) / len(success_rates), 2) if success_rates else 0,
                'avg_cpu_percent': round(sum(cpu_usage) / len(cpu_usage), 2) if cpu_usage else 0,
                'avg_memory_percent': round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
                'total_measurements': len(recent_metrics)
            }
            
            # Tendance des performances
            if len(recent_metrics) >= 2:
                first_half = recent_metrics[:len(recent_metrics)//2]
                second_half = recent_metrics[len(recent_metrics)//2:]
                
                first_avg_response = sum(m['rag']['avg_response_time_ms'] for m in first_half if 'rag' in m) / len(first_half)
                second_avg_response = sum(m['rag']['avg_response_time_ms'] for m in second_half if 'rag' in m) / len(second_half)
                
                if second_avg_response > first_avg_response * 1.1:
                    performance_trend = 'degrading'
                elif second_avg_response < first_avg_response * 0.9:
                    performance_trend = 'improving'
                else:
                    performance_trend = 'stable'
            else:
                performance_trend = 'insufficient_data'
            
            # Recommandations basées sur les performances
            recommendations = []
            if performance_stats['avg_response_time_ms'] > 500:
                recommendations.append("Optimiser les requêtes de recherche")
            if performance_stats['avg_success_rate_percent'] < 95:
                recommendations.append("Améliorer la gestion d'erreurs")
            if performance_stats['avg_cpu_percent'] > 70:
                recommendations.append("Optimiser l'utilisation CPU")
            if performance_stats['avg_memory_percent'] > 80:
                recommendations.append("Optimiser l'utilisation mémoire")
            
            return {
                'success': True,
                'period_hours': hours,
                'performance_stats': performance_stats,
                'performance_trend': performance_trend,
                'recommendations': recommendations,
                'data_points': len(recent_metrics)
            }
            
        except Exception as e:
            logger.error(f"Erreur génération rapport: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des alertes"""
        try:
            # Alertes non acquittées
            unacknowledged = [a for a in self.alerts_history if not a.get('acknowledged', False)]
            
            # Alertes par niveau
            critical_alerts = [a for a in unacknowledged if a['level'] == 'critical']
            warning_alerts = [a for a in unacknowledged if a['level'] == 'warning']
            
            # Alertes récentes (dernières 24h)
            recent_cutoff = timezone.now() - timedelta(hours=24)
            recent_alerts = [
                a for a in self.alerts_history
                if timezone.datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) >= recent_cutoff
            ]
            
            return {
                'total_alerts': len(self.alerts_history),
                'unacknowledged_alerts': len(unacknowledged),
                'critical_alerts': len(critical_alerts),
                'warning_alerts': len(warning_alerts),
                'recent_alerts_24h': len(recent_alerts),
                'latest_alert': self.alerts_history[-1] if self.alerts_history else None
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé alertes: {e}")
            return {
                'error': str(e),
                'total_alerts': 0
            }
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """Acquitte une alerte"""
        try:
            if 0 <= alert_index < len(self.alerts_history):
                self.alerts_history[alert_index]['acknowledged'] = True
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur acquittement alerte: {e}")
            return False
    
    def clear_old_data(self, days: int = 30) -> Dict[str, Any]:
        """Nettoie les anciennes données de monitoring"""
        try:
            cutoff_time = timezone.now() - timedelta(days=days)
            
            # Nettoyer les métriques
            initial_metrics = len(self.metrics_history)
            self.metrics_history = [
                m for m in self.metrics_history
                if timezone.datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) >= cutoff_time
            ]
            cleaned_metrics = initial_metrics - len(self.metrics_history)
            
            # Nettoyer les alertes
            initial_alerts = len(self.alerts_history)
            self.alerts_history = [
                a for a in self.alerts_history
                if timezone.datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) >= cutoff_time
            ]
            cleaned_alerts = initial_alerts - len(self.alerts_history)
            
            return {
                'success': True,
                'cleaned_metrics': cleaned_metrics,
                'cleaned_alerts': cleaned_alerts,
                'remaining_metrics': len(self.metrics_history),
                'remaining_alerts': len(self.alerts_history)
            }
            
        except Exception as e:
            logger.error(f"Erreur nettoyage données: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Instance globale
advanced_monitoring_service = AdvancedMonitoringService()
