"""
Service d'optimisation intelligente pour la Phase 6.
Intègre tous les services existants pour une performance maximale.
"""
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from mai.embedding_service import embedding_service
from mai.vector_search_service import vector_search_service
from mai.cache_service import cache_service as advanced_cache_service
from mai.vector_index_service import vector_index_service
from mai.monitoring_service import advanced_monitoring_service
from mai.models import DocumentEmbedding, RAGSearchLog

logger = logging.getLogger(__name__)

class IntelligentOptimizationService:
    """Service d'optimisation intelligente qui orchestre tous les services"""
    
    def __init__(self):
        self.optimization_config = self._load_optimization_config()
        self.performance_history = []
        self.optimization_schedule = []
        
    def _load_optimization_config(self) -> Dict[str, Any]:
        """Charge la configuration d'optimisation"""
        return {
            'auto_optimization': {
                'enabled': True,
                'interval_hours': 6,
                'performance_threshold': 0.8,
                'cache_warmup_enabled': True
            },
            'performance_targets': {
                'response_time_ms': 200,
                'cache_hit_rate': 0.85,
                'success_rate': 0.98,
                'throughput_qps': 50
            },
            'optimization_strategies': {
                'cache_optimization': True,
                'index_optimization': True,
                'embedding_optimization': True,
                'monitoring_optimization': True
            }
        }
    
    def run_comprehensive_optimization(self) -> Dict[str, Any]:
        """Exécute une optimisation complète du système"""
        start_time = time.time()
        optimization_results = {}
        
        try:
            logger.info("🚀 Démarrage de l'optimisation complète du système RAG")
            
            # 1. Optimisation du cache local (Redis désactivé)
            logger.info("📦 Optimisation du cache local (Redis désactivé)...")
            cache_result = self._optimize_cache()
            optimization_results['cache'] = cache_result
            
            # 2. Optimisation des index vectoriels
            logger.info("🔍 Optimisation des index vectoriels...")
            index_result = self._optimize_vector_indexes()
            optimization_results['indexes'] = index_result
            
            # 3. Optimisation des embeddings
            logger.info("🧠 Optimisation des embeddings...")
            embedding_result = self._optimize_embeddings()
            optimization_results['embeddings'] = embedding_result
            
            # 4. Optimisation du monitoring
            logger.info("📊 Optimisation du monitoring...")
            monitoring_result = self._optimize_monitoring()
            optimization_results['monitoring'] = monitoring_result
            
            # 5. Préchauffage intelligent
            logger.info("🔥 Préchauffage intelligent du système...")
            warmup_result = self._intelligent_warmup()
            optimization_results['warmup'] = warmup_result
            
            # 6. Validation des performances
            logger.info("✅ Validation des performances...")
            validation_result = self._validate_performance()
            optimization_results['validation'] = validation_result
            
            total_duration = time.time() - start_time
            
            # Enregistrer l'optimisation
            self._record_optimization(optimization_results, total_duration)
            
            return {
                'success': True,
                'duration_seconds': round(total_duration, 2),
                'optimization_results': optimization_results,
                'message': 'Optimisation complète terminée avec succès'
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation complète: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': round(time.time() - start_time, 2)
            }
    
    def _optimize_cache(self) -> Dict[str, Any]:
        """Optimise le cache local (Redis désactivé)"""
        try:
            # 1. Vérifier la santé du cache local
            cache_health = advanced_cache_service.health_check()
            
            # 2. Optimiser le cache local si nécessaire
            if cache_health['status'] in ['warning', 'critical']:
                optimization_result = advanced_cache_service.optimize_cache()
            else:
                optimization_result = {'success': True, 'message': 'Cache local déjà optimisé'}
            
            # 3. Préchauffer le cache local (si méthode disponible)
            try:
                warmup_result = advanced_cache_service.warm_up_cache()
            except AttributeError:
                warmup_result = {'success': True, 'message': 'Warm-up non disponible pour cache local'}
            
            # 4. Obtenir les statistiques finales
            final_stats = advanced_cache_service.get_cache_stats()
            
            return {
                'health_before': cache_health,
                'optimization': optimization_result,
                'warmup': warmup_result,
                'final_stats': final_stats
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation cache: {e}")
            return {'error': str(e)}
    
    def _optimize_vector_indexes(self) -> Dict[str, Any]:
        """Optimise les index vectoriels"""
        try:
            # 1. Analyser les performances actuelles
            performance_analysis = vector_index_service.analyze_index_performance()
            
            # 2. Vérifier si une reindexation est nécessaire
            reindex_result = vector_index_service.reindex_if_needed()
            
            # 3. Optimiser l'index existant
            optimization_result = vector_index_service.optimize_existing_index()
            
            # 4. Vérifier la santé de l'index
            health_check = vector_index_service.get_index_health()
            
            return {
                'performance_analysis': performance_analysis,
                'reindex_check': reindex_result,
                'optimization': optimization_result,
                'health_check': health_check
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation index: {e}")
            return {'error': str(e)}
    
    def _optimize_embeddings(self) -> Dict[str, Any]:
        """Optimise le service d'embeddings"""
        try:
            # 1. Vérifier la configuration du modèle
            model_info = embedding_service.get_model_info()
            
            # 2. Nettoyer le cache des embeddings si nécessaire
            cache_clear_result = embedding_service.clear_cache()
            
            # 3. Valider quelques embeddings existants
            validation_results = []
            sample_docs = DocumentEmbedding.objects.all()[:5]
            
            for doc in sample_docs:
                if doc.embedding:
                    is_valid = embedding_service.validate_embedding(doc.embedding)
                    validation_results.append({
                        'doc_id': doc.id,
                        'is_valid': is_valid,
                        'dimension': len(doc.embedding) if doc.embedding else 0
                    })
            
            # 4. Obtenir les statistiques du cache
            cache_stats = embedding_service.get_cache_stats()
            
            return {
                'model_info': model_info,
                'cache_clear': cache_clear_result,
                'validation_results': validation_results,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation embeddings: {e}")
            return {'error': str(e)}
    
    def _optimize_monitoring(self) -> Dict[str, Any]:
        """Optimise le système de monitoring"""
        try:
            # 1. Collecter les métriques actuelles
            current_metrics = advanced_monitoring_service.collect_system_metrics()
            
            # 2. Vérifier la santé du système
            health_check = advanced_monitoring_service.check_system_health()
            
            # 3. Nettoyer les anciennes données
            cleanup_result = advanced_monitoring_service.clear_old_data(days=7)
            
            # 4. Générer un rapport de performance
            performance_report = advanced_monitoring_service.get_performance_report(hours=24)
            
            return {
                'current_metrics': current_metrics,
                'health_check': health_check,
                'cleanup': cleanup_result,
                'performance_report': performance_report
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation monitoring: {e}")
            return {'error': str(e)}
    
    def _intelligent_warmup(self) -> Dict[str, Any]:
        """Préchauffage intelligent du système"""
        try:
            warmup_results = {}
            
            # 1. Préchauffer les embeddings fréquents
            frequent_queries = [
                "Quelle est la date d'inauguration de la SAR ?",
                "Quelle est la capacité de la SAR ?",
                "Quels sont les produits de la SAR ?",
                "Qui est le président de la SAR ?",
                "Où se trouve la SAR ?",
                "Quelle est l'histoire de la SAR ?",
                "Quels sont les clients de la SAR ?",
                "Comment fonctionne la SAR ?"
            ]
            
            embedding_warmup_count = 0
            for query in frequent_queries:
                if not advanced_cache_service.get_cached_embedding(query):
                    try:
                        embedding = embedding_service.generate_embedding(query)
                        advanced_cache_service.cache_embedding(query, embedding)
                        embedding_warmup_count += 1
                    except Exception as e:
                        logger.warning(f"Erreur warmup embedding pour '{query}': {e}")
            
            warmup_results['embeddings_warmed'] = embedding_warmup_count
            
            # 2. Préchauffer les recherches fréquentes
            search_warmup_count = 0
            for query in frequent_queries:
                try:
                    results = vector_search_service.search_similar(query, limit=3, threshold=0.7)
                    if results:
                        # Mettre en cache les résultats
                        cache_data = []
                        for doc in results:
                            cache_data.append({
                                'id': doc.id,
                                'content': doc.content_text,
                                'metadata': doc.metadata,
                                'similarity': getattr(doc, 'similarity', 0.0)
                            })
                        advanced_cache_service.cache_search(query, 3, 0.7, cache_data)
                        search_warmup_count += 1
                except Exception as e:
                    logger.warning(f"Erreur warmup search pour '{query}': {e}")
            
            warmup_results['searches_warmed'] = search_warmup_count
            
            # 3. Préchauffer le monitoring
            try:
                advanced_monitoring_service.collect_system_metrics()
                warmup_results['monitoring_warmed'] = True
            except Exception as e:
                logger.warning(f"Erreur warmup monitoring: {e}")
                warmup_results['monitoring_warmed'] = False
            
            return warmup_results
            
        except Exception as e:
            logger.error(f"Erreur intelligent warmup: {e}")
            return {'error': str(e)}
    
    def _validate_performance(self) -> Dict[str, Any]:
        """Valide les performances après optimisation"""
        try:
            validation_results = {}
            
            # 1. Test de performance des embeddings
            start_time = time.time()
            test_embedding = embedding_service.generate_embedding("Test de performance")
            embedding_time = (time.time() - start_time) * 1000
            validation_results['embedding_time_ms'] = round(embedding_time, 2)
            
            # 2. Test de performance de recherche
            start_time = time.time()
            search_results = vector_search_service.search_similar(
                "Test de performance de recherche", 
                limit=3, 
                threshold=0.7
            )
            search_time = (time.time() - start_time) * 1000
            validation_results['search_time_ms'] = round(search_time, 2)
            validation_results['search_results_count'] = len(search_results)
            
            # 3. Test de performance du cache
            cache_stats = advanced_cache_service.get_cache_stats()
            validation_results['cache_stats'] = cache_stats
            
            # 4. Test de performance du monitoring
            monitoring_metrics = advanced_monitoring_service.collect_system_metrics()
            validation_results['monitoring_metrics'] = monitoring_metrics
            
            # 5. Calculer le score de performance global
            performance_score = self._calculate_performance_score(validation_results)
            validation_results['performance_score'] = performance_score
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Erreur validation performance: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_score(self, validation_results: Dict[str, Any]) -> int:
        """Calcule un score de performance global"""
        try:
            score = 100
            
            # Pénalités basées sur les temps de réponse
            if validation_results.get('embedding_time_ms', 0) > 100:
                score -= 20
            elif validation_results.get('embedding_time_ms', 0) > 50:
                score -= 10
            
            if validation_results.get('search_time_ms', 0) > 500:
                score -= 30
            elif validation_results.get('search_time_ms', 0) > 200:
                score -= 15
            
            # Bonus pour le cache
            cache_stats = validation_results.get('cache_stats', {})
            if cache_stats.get('status') == 'active':
                hit_rate = cache_stats.get('hit_rate', 0)
                if hit_rate > 80:
                    score += 10
                elif hit_rate > 60:
                    score += 5
            
            return max(0, min(100, score))
            
        except Exception:
            return 50  # Score par défaut en cas d'erreur
    
    def _record_optimization(self, results: Dict[str, Any], duration: float) -> None:
        """Enregistre les résultats de l'optimisation"""
        try:
            optimization_record = {
                'timestamp': timezone.now().isoformat(),
                'duration_seconds': duration,
                'results': results,
                'success': results.get('success', False)
            }
            
            self.performance_history.append(optimization_record)
            
            # Garder seulement les 100 dernières optimisations
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
                
        except Exception as e:
            logger.error(f"Erreur enregistrement optimisation: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel de l'optimisation"""
        try:
            # Vérifier la santé de tous les services
            cache_health = advanced_cache_service.get_cache_health()
            index_health = vector_index_service.get_index_health()
            monitoring_health = advanced_monitoring_service.check_system_health()
            
            # Calculer un score de santé global
            health_scores = []
            if cache_health.get('status') == 'excellent':
                health_scores.append(100)
            elif cache_health.get('status') == 'good':
                health_scores.append(80)
            elif cache_health.get('status') == 'warning':
                health_scores.append(60)
            else:
                health_scores.append(40)
            
            if index_health.get('status') == 'healthy':
                health_scores.append(100)
            elif index_health.get('status') == 'warning':
                health_scores.append(70)
            else:
                health_scores.append(50)
            
            if monitoring_health.get('status') == 'excellent':
                health_scores.append(100)
            elif monitoring_health.get('status') == 'good':
                health_scores.append(80)
            else:
                health_scores.append(60)
            
            overall_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
            
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_health_score': round(overall_health_score, 2),
                'cache_health': cache_health,
                'index_health': index_health,
                'monitoring_health': monitoring_health,
                'optimization_history_count': len(self.performance_history),
                'last_optimization': self.performance_history[-1] if self.performance_history else None
            }
            
        except Exception as e:
            logger.error(f"Erreur statut optimisation: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def schedule_automatic_optimization(self) -> Dict[str, Any]:
        """Planifie une optimisation automatique"""
        try:
            from datetime import timedelta
            
            next_optimization = timezone.now() + timedelta(
                hours=self.optimization_config['auto_optimization']['interval_hours']
            )
            
            self.optimization_schedule.append({
                'scheduled_time': next_optimization.isoformat(),
                'type': 'automatic',
                'status': 'scheduled'
            })
            
            return {
                'success': True,
                'scheduled_time': next_optimization.isoformat(),
                'interval_hours': self.optimization_config['auto_optimization']['interval_hours']
            }
            
        except Exception as e:
            logger.error(f"Erreur planification optimisation: {e}")
            return {'error': str(e)}

# Instance globale
intelligent_optimization_service = IntelligentOptimizationService()
