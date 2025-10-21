"""
Gestionnaire de déploiement intelligent pour la Phase 4.
Gère le déploiement progressif, les tests A/B et le monitoring.
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.db import models
from mai.models import RAGSearchLog, DocumentEmbedding
from mai.vector_search_service import vector_search_service
from mai.services import MAIService

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Gestionnaire de déploiement intelligent"""
    
    def __init__(self):
        self.mai_service = MAIService()
        self.vector_service = vector_search_service
        self.deployment_config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Charge la configuration de déploiement"""
        return {
            'phases': {
                'alpha': {
                    'name': 'Phase Alpha',
                    'description': 'Test interne avec 5% du trafic',
                    'traffic_percentage': 5,
                    'duration_hours': 24,
                    'success_threshold': 0.8,
                    'performance_threshold_ms': 1000
                },
                'beta': {
                    'name': 'Phase Beta', 
                    'description': 'Test élargi avec 25% du trafic',
                    'traffic_percentage': 25,
                    'duration_hours': 72,
                    'success_threshold': 0.85,
                    'performance_threshold_ms': 800
                },
                'gamma': {
                    'name': 'Phase Gamma',
                    'description': 'Déploiement large avec 75% du trafic',
                    'traffic_percentage': 75,
                    'duration_hours': 168,
                    'success_threshold': 0.9,
                    'performance_threshold_ms': 600
                },
                'production': {
                    'name': 'Production',
                    'description': 'Déploiement complet à 100%',
                    'traffic_percentage': 100,
                    'duration_hours': None,
                    'success_threshold': 0.95,
                    'performance_threshold_ms': 500
                }
            },
            'current_phase': 'alpha',
            'start_time': None,
            'rollback_threshold': 0.7,
            'monitoring_interval_minutes': 15
        }
    
    def start_deployment(self, phase: str = 'alpha') -> Dict[str, Any]:
        """Démarre le déploiement à la phase spécifiée"""
        try:
            if phase not in self.deployment_config['phases']:
                raise ValueError(f"Phase invalide: {phase}")
            
            self.deployment_config['current_phase'] = phase
            self.deployment_config['start_time'] = timezone.now()
            
            # Initialiser les métriques de base
            self._initialize_metrics()
            
            logger.info(f"Déploiement démarré - Phase: {phase}")
            
            return {
                'success': True,
                'phase': phase,
                'start_time': self.deployment_config['start_time'].isoformat(),
                'config': self.deployment_config['phases'][phase]
            }
            
        except Exception as e:
            logger.error(f"Erreur démarrage déploiement: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Récupère le statut actuel du déploiement"""
        try:
            current_phase = self.deployment_config['current_phase']
            phase_config = self.deployment_config['phases'][current_phase]
            start_time = self.deployment_config['start_time']
            
            if not start_time:
                return {
                    'status': 'not_started',
                    'message': 'Aucun déploiement en cours'
                }
            
            # Calculer la durée écoulée
            elapsed = timezone.now() - start_time
            elapsed_hours = elapsed.total_seconds() / 3600
            
            # Récupérer les métriques de la phase
            metrics = self._get_phase_metrics(current_phase, start_time)
            
            # Déterminer le statut
            status = self._determine_deployment_status(metrics, phase_config)
            
            return {
                'status': status,
                'phase': current_phase,
                'elapsed_hours': elapsed_hours,
                'metrics': metrics,
                'config': phase_config,
                'next_phase_ready': self._is_next_phase_ready(metrics, phase_config)
            }
            
        except Exception as e:
            logger.error(f"Erreur statut déploiement: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def promote_to_next_phase(self) -> Dict[str, Any]:
        """Promouvoir vers la phase suivante"""
        try:
            current_phase = self.deployment_config['current_phase']
            phases = list(self.deployment_config['phases'].keys())
            current_index = phases.index(current_phase)
            
            if current_index >= len(phases) - 1:
                return {
                    'success': False,
                    'message': 'Déjà en phase de production'
                }
            
            next_phase = phases[current_index + 1]
            
            # Vérifier que la phase actuelle est prête
            status = self.get_deployment_status()
            if not status.get('next_phase_ready', False):
                return {
                    'success': False,
                    'message': 'Phase actuelle pas encore prête pour la promotion'
                }
            
            # Promouvoir vers la phase suivante
            self.deployment_config['current_phase'] = next_phase
            self.deployment_config['start_time'] = timezone.now()
            
            logger.info(f"Promotion vers la phase: {next_phase}")
            
            return {
                'success': True,
                'previous_phase': current_phase,
                'new_phase': next_phase,
                'start_time': self.deployment_config['start_time'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur promotion phase: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def rollback_deployment(self) -> Dict[str, Any]:
        """Effectuer un rollback vers l'heuristique"""
        try:
            current_phase = self.deployment_config['current_phase']
            
            # Forcer l'utilisation de l'heuristique uniquement
            self.deployment_config['current_phase'] = 'heuristic_only'
            self.deployment_config['start_time'] = timezone.now()
            
            logger.warning(f"Rollback effectué depuis la phase: {current_phase}")
            
            return {
                'success': True,
                'rollback_from': current_phase,
                'rollback_time': self.deployment_config['start_time'].isoformat(),
                'message': 'Système basculé vers l\'heuristique uniquement'
            }
            
        except Exception as e:
            logger.error(f"Erreur rollback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _initialize_metrics(self):
        """Initialise les métriques de base"""
        try:
            # Créer un log de démarrage
            RAGSearchLog.objects.create(
                query='DEPLOYMENT_START',
                method='deployment',
                results_count=0,
                response_time_ms=0,
                success=True,
                error_message=f"Déploiement démarré - Phase: {self.deployment_config['current_phase']}"
            )
        except Exception as e:
            logger.error(f"Erreur initialisation métriques: {e}")
    
    def _get_phase_metrics(self, phase: str, start_time: datetime) -> Dict[str, Any]:
        """Récupère les métriques pour une phase donnée"""
        try:
            # Récupérer les logs de la phase
            logs = RAGSearchLog.objects.filter(
                created_at__gte=start_time,
                method__in=['vectorial', 'heuristic', 'hybrid']
            )
            
            total_searches = logs.count()
            successful_searches = logs.filter(success=True).count()
            failed_searches = logs.filter(success=False).count()
            
            # Calculer les métriques de performance
            avg_response_time = logs.aggregate(
                avg_time=models.Avg('response_time_ms')
            )['avg_time'] or 0
            
            # Métriques par méthode
            method_stats = {}
            for method in ['vectorial', 'heuristic', 'hybrid']:
                method_logs = logs.filter(method=method)
                method_stats[method] = {
                    'count': method_logs.count(),
                    'success_rate': (method_logs.filter(success=True).count() / method_logs.count() * 100) if method_logs.count() > 0 else 0,
                    'avg_response_time': method_logs.aggregate(
                        avg_time=models.Avg('response_time_ms')
                    )['avg_time'] or 0
                }
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'failed_searches': failed_searches,
                'success_rate': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
                'avg_response_time_ms': avg_response_time,
                'method_stats': method_stats,
                'phase_duration_hours': (timezone.now() - start_time).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération métriques: {e}")
            return {}
    
    def _determine_deployment_status(self, metrics: Dict[str, Any], phase_config: Dict[str, Any]) -> str:
        """Détermine le statut du déploiement basé sur les métriques"""
        try:
            success_rate = metrics.get('success_rate', 0) / 100
            avg_response_time = metrics.get('avg_response_time_ms', 0)
            phase_duration = metrics.get('phase_duration_hours', 0)
            
            # Vérifier les seuils
            success_threshold = phase_config.get('success_threshold', 0.8)
            performance_threshold = phase_config.get('performance_threshold_ms', 1000)
            duration_threshold = phase_config.get('duration_hours', 24)
            
            # Statut basé sur les métriques
            if success_rate < self.deployment_config['rollback_threshold']:
                return 'rollback_required'
            elif success_rate >= success_threshold and avg_response_time <= performance_threshold:
                if duration_threshold and phase_duration >= duration_threshold:
                    return 'ready_for_next_phase'
                else:
                    return 'performing_well'
            elif success_rate >= success_threshold:
                return 'performance_issues'
            else:
                return 'needs_improvement'
                
        except Exception as e:
            logger.error(f"Erreur détermination statut: {e}")
            return 'error'
    
    def _is_next_phase_ready(self, metrics: Dict[str, Any], phase_config: Dict[str, Any]) -> bool:
        """Vérifie si la phase est prête pour la promotion"""
        try:
            success_rate = metrics.get('success_rate', 0) / 100
            avg_response_time = metrics.get('avg_response_time_ms', 0)
            phase_duration = metrics.get('phase_duration_hours', 0)
            
            success_threshold = phase_config.get('success_threshold', 0.8)
            performance_threshold = phase_config.get('performance_threshold_ms', 1000)
            duration_threshold = phase_config.get('duration_hours', 24)
            
            return (
                success_rate >= success_threshold and
                avg_response_time <= performance_threshold and
                (not duration_threshold or phase_duration >= duration_threshold)
            )
            
        except Exception as e:
            logger.error(f"Erreur vérification promotion: {e}")
            return False
    
    def get_deployment_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les métriques"""
        try:
            recommendations = []
            status = self.get_deployment_status()
            metrics = status.get('metrics', {})
            
            success_rate = metrics.get('success_rate', 0)
            avg_response_time = metrics.get('avg_response_time_ms', 0)
            method_stats = metrics.get('method_stats', {})
            
            # Recommandations basées sur le taux de succès
            if success_rate < 80:
                recommendations.append("Taux de succès faible - Vérifier la qualité des embeddings")
            elif success_rate < 90:
                recommendations.append("Taux de succès correct - Surveiller les performances")
            else:
                recommendations.append("Excellent taux de succès - Prêt pour la promotion")
            
            # Recommandations basées sur les performances
            if avg_response_time > 1000:
                recommendations.append("Temps de réponse élevé - Optimiser les requêtes vectorielles")
            elif avg_response_time > 500:
                recommendations.append("Temps de réponse acceptable - Surveiller la charge")
            else:
                recommendations.append("Performances excellentes - Système optimisé")
            
            # Recommandations basées sur les méthodes
            vectorial_stats = method_stats.get('vectorial', {})
            if vectorial_stats.get('count', 0) > 0:
                vectorial_success = vectorial_stats.get('success_rate', 0)
                if vectorial_success < 85:
                    recommendations.append("Recherche vectorielle peu fiable - Vérifier les seuils de similarité")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return ["Erreur lors de la génération des recommandations"]

# Instance globale
deployment_manager = DeploymentManager()
