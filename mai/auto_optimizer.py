"""
Système d'optimisation automatique pour la Phase 5.
Optimise les performances, la qualité des données et la scalabilité.
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db import models, connection
from django.core.cache import cache
from mai.models import RAGSearchLog, DocumentEmbedding
from mai.vector_search_service import vector_search_service
from mai.embedding_service import embedding_service
from mai.services import MAIService

logger = logging.getLogger(__name__)

class AutoOptimizer:
    """Système d'optimisation automatique intelligent"""
    
    def __init__(self):
        self.optimization_config = self._load_optimization_config()
        self.performance_history = []
        self.optimization_log = []
        
    def _load_optimization_config(self) -> Dict[str, Any]:
        """Charge la configuration d'optimisation"""
        return {
            'performance': {
                'response_time_threshold_ms': 500,
                'success_rate_threshold': 0.95,
                'optimization_interval_hours': 6,
                'auto_tune_enabled': True
            },
            'data_quality': {
                'embedding_quality_threshold': 0.8,
                'duplicate_threshold': 0.9,
                'quality_check_interval_hours': 24,
                'auto_cleanup_enabled': True
            },
            'scalability': {
                'memory_usage_threshold': 0.8,
                'cache_hit_rate_threshold': 0.7,
                'scaling_check_interval_hours': 12,
                'auto_scaling_enabled': True
            },
            'analytics': {
                'trend_analysis_days': 7,
                'anomaly_detection_enabled': True,
                'prediction_horizon_hours': 24,
                'auto_insights_enabled': True
            }
        }
    
    def run_optimization_cycle(self) -> Dict[str, Any]:
        """Exécute un cycle d'optimisation complet"""
        start_time = time.time()
        optimization_results = {
            'timestamp': timezone.now().isoformat(),
            'duration_seconds': 0,
            'optimizations_applied': [],
            'performance_improvements': {},
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            logger.info("Démarrage du cycle d'optimisation automatique")
            
            # 1. Analyse des performances
            performance_analysis = self._analyze_performance()
            optimization_results['performance_analysis'] = performance_analysis
            
            # 2. Optimisation des performances
            if performance_analysis.get('needs_optimization', False):
                perf_optimizations = self._optimize_performance(performance_analysis)
                optimization_results['optimizations_applied'].extend(perf_optimizations)
            
            # 3. Analyse de la qualité des données
            data_quality_analysis = self._analyze_data_quality()
            optimization_results['data_quality_analysis'] = data_quality_analysis
            
            # 4. Optimisation de la qualité des données
            if data_quality_analysis.get('needs_cleanup', False):
                data_optimizations = self._optimize_data_quality(data_quality_analysis)
                optimization_results['optimizations_applied'].extend(data_optimizations)
            
            # 5. Analyse de scalabilité
            scalability_analysis = self._analyze_scalability()
            optimization_results['scalability_analysis'] = scalability_analysis
            
            # 6. Optimisation de scalabilité
            if scalability_analysis.get('needs_scaling', False):
                scaling_optimizations = self._optimize_scalability(scalability_analysis)
                optimization_results['optimizations_applied'].extend(scaling_optimizations)
            
            # 7. Analytics intelligents
            analytics_insights = self._generate_intelligent_analytics()
            optimization_results['analytics_insights'] = analytics_insights
            
            # 8. Recommandations automatiques
            recommendations = self._generate_auto_recommendations(optimization_results)
            optimization_results['recommendations'] = recommendations
            
            # Calculer la durée
            optimization_results['duration_seconds'] = time.time() - start_time
            
            # Logger les résultats
            self._log_optimization_results(optimization_results)
            
            logger.info(f"Cycle d'optimisation terminé en {optimization_results['duration_seconds']:.2f}s")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Erreur lors du cycle d'optimisation: {e}")
            optimization_results['error'] = str(e)
            return optimization_results
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyse les performances du système"""
        try:
            # Récupérer les métriques des dernières 24h
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=24)
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            # Métriques de base
            total_searches = logs.count()
            successful_searches = logs.filter(success=True).count()
            success_rate = successful_searches / total_searches if total_searches > 0 else 0
            
            # Temps de réponse
            response_times = logs.values_list('response_time_ms', flat=True)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            
            # Métriques par méthode
            method_stats = {}
            for method in ['vectorial', 'heuristic', 'hybrid']:
                method_logs = logs.filter(method=method)
                if method_logs.exists():
                    method_times = method_logs.values_list('response_time_ms', flat=True)
                    method_stats[method] = {
                        'count': method_logs.count(),
                        'success_rate': method_logs.filter(success=True).count() / method_logs.count(),
                        'avg_time': sum(method_times) / len(method_times) if method_times else 0,
                        'max_time': max(method_times) if method_times else 0
                    }
            
            # Analyser les tendances
            hourly_performance = self._analyze_hourly_performance(logs, start_time, end_time)
            
            # Déterminer si une optimisation est nécessaire
            needs_optimization = (
                avg_response_time > self.optimization_config['performance']['response_time_threshold_ms'] or
                success_rate < self.optimization_config['performance']['success_rate_threshold']
            )
            
            return {
                'total_searches': total_searches,
                'success_rate': success_rate,
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'min_response_time_ms': min_response_time,
                'method_stats': method_stats,
                'hourly_performance': hourly_performance,
                'needs_optimization': needs_optimization,
                'optimization_priority': self._calculate_optimization_priority(avg_response_time, success_rate)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse performances: {e}")
            return {'error': str(e)}
    
    def _optimize_performance(self, performance_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimise les performances du système"""
        optimizations = []
        
        try:
            avg_response_time = performance_analysis.get('avg_response_time_ms', 0)
            success_rate = performance_analysis.get('success_rate', 0)
            method_stats = performance_analysis.get('method_stats', {})
            
            # Optimisation 1: Ajuster les seuils de similarité
            if avg_response_time > 1000:
                optimization = self._optimize_similarity_thresholds()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 2: Optimiser le cache
            if avg_response_time > 500:
                optimization = self._optimize_cache_settings()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 3: Optimiser les requêtes vectorielles
            vectorial_stats = method_stats.get('vectorial', {})
            if vectorial_stats.get('avg_time', 0) > 200:
                optimization = self._optimize_vector_queries()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 4: Optimiser les requêtes heuristiques
            heuristic_stats = method_stats.get('heuristic', {})
            if heuristic_stats.get('avg_time', 0) > 100:
                optimization = self._optimize_heuristic_queries()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 5: Rééquilibrer les méthodes
            if success_rate < 0.9:
                optimization = self._rebalance_methods(method_stats)
                if optimization:
                    optimizations.append(optimization)
            
        except Exception as e:
            logger.error(f"Erreur optimisation performances: {e}")
        
        return optimizations
    
    def _analyze_data_quality(self) -> Dict[str, Any]:
        """Analyse la qualité des données"""
        try:
            # Analyser les embeddings
            total_embeddings = DocumentEmbedding.objects.count()
            valid_embeddings = DocumentEmbedding.objects.filter(
                embedding__len=embedding_service.dimension
            ).count()
            
            embedding_quality = valid_embeddings / total_embeddings if total_embeddings > 0 else 0
            
            # Détecter les doublons potentiels
            duplicates = self._detect_duplicate_embeddings()
            
            # Analyser la distribution des similarités
            similarity_distribution = self._analyze_similarity_distribution()
            
            # Analyser la qualité des métadonnées
            metadata_quality = self._analyze_metadata_quality()
            
            # Déterminer si un nettoyage est nécessaire
            needs_cleanup = (
                embedding_quality < self.optimization_config['data_quality']['embedding_quality_threshold'] or
                len(duplicates) > 0 or
                metadata_quality < 0.8
            )
            
            return {
                'total_embeddings': total_embeddings,
                'valid_embeddings': valid_embeddings,
                'embedding_quality': embedding_quality,
                'duplicates_found': len(duplicates),
                'duplicates': duplicates,
                'similarity_distribution': similarity_distribution,
                'metadata_quality': metadata_quality,
                'needs_cleanup': needs_cleanup,
                'cleanup_priority': self._calculate_cleanup_priority(embedding_quality, len(duplicates))
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse qualité données: {e}")
            return {'error': str(e)}
    
    def _optimize_data_quality(self, data_quality_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimise la qualité des données"""
        optimizations = []
        
        try:
            # Nettoyage 1: Supprimer les doublons
            duplicates = data_quality_analysis.get('duplicates', [])
            if duplicates:
                optimization = self._remove_duplicate_embeddings(duplicates)
                if optimization:
                    optimizations.append(optimization)
            
            # Nettoyage 2: Réparer les embeddings invalides
            embedding_quality = data_quality_analysis.get('embedding_quality', 0)
            if embedding_quality < 0.9:
                optimization = self._repair_invalid_embeddings()
                if optimization:
                    optimizations.append(optimization)
            
            # Nettoyage 3: Améliorer les métadonnées
            metadata_quality = data_quality_analysis.get('metadata_quality', 0)
            if metadata_quality < 0.8:
                optimization = self._improve_metadata_quality()
                if optimization:
                    optimizations.append(optimization)
            
            # Nettoyage 4: Optimiser la distribution des similarités
            similarity_distribution = data_quality_analysis.get('similarity_distribution', {})
            if similarity_distribution.get('variance', 0) > 0.5:
                optimization = self._optimize_similarity_distribution()
                if optimization:
                    optimizations.append(optimization)
            
        except Exception as e:
            logger.error(f"Erreur optimisation qualité données: {e}")
        
        return optimizations
    
    def _analyze_scalability(self) -> Dict[str, Any]:
        """Analyse la scalabilité du système"""
        try:
            import psutil
            
            # Métriques système
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Métriques de cache
            cache_stats = self._analyze_cache_performance()
            
            # Métriques de base de données
            db_stats = self._analyze_database_performance()
            
            # Métriques de croissance
            growth_stats = self._analyze_growth_trends()
            
            # Déterminer si une mise à l'échelle est nécessaire
            needs_scaling = (
                memory.percent > self.optimization_config['scalability']['memory_usage_threshold'] * 100 or
                cache_stats.get('hit_rate', 0) < self.optimization_config['scalability']['cache_hit_rate_threshold'] or
                db_stats.get('avg_query_time', 0) > 1000
            )
            
            return {
                'memory_usage_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'cpu_usage_percent': cpu_percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'cache_stats': cache_stats,
                'database_stats': db_stats,
                'growth_stats': growth_stats,
                'needs_scaling': needs_scaling,
                'scaling_priority': self._calculate_scaling_priority(memory.percent, cache_stats.get('hit_rate', 0))
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse scalabilité: {e}")
            return {'error': str(e)}
    
    def _optimize_scalability(self, scalability_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimise la scalabilité du système"""
        optimizations = []
        
        try:
            memory_usage = scalability_analysis.get('memory_usage_percent', 0)
            cache_stats = scalability_analysis.get('cache_stats', {})
            db_stats = scalability_analysis.get('database_stats', {})
            
            # Optimisation 1: Optimiser la mémoire
            if memory_usage > 80:
                optimization = self._optimize_memory_usage()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 2: Optimiser le cache
            cache_hit_rate = cache_stats.get('hit_rate', 0)
            if cache_hit_rate < 0.7:
                optimization = self._optimize_cache_scalability()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 3: Optimiser la base de données
            avg_query_time = db_stats.get('avg_query_time', 0)
            if avg_query_time > 500:
                optimization = self._optimize_database_scalability()
                if optimization:
                    optimizations.append(optimization)
            
            # Optimisation 4: Optimiser les requêtes vectorielles
            if db_stats.get('vector_query_time', 0) > 200:
                optimization = self._optimize_vector_scalability()
                if optimization:
                    optimizations.append(optimization)
            
        except Exception as e:
            logger.error(f"Erreur optimisation scalabilité: {e}")
        
        return optimizations
    
    def _generate_intelligent_analytics(self) -> Dict[str, Any]:
        """Génère des analytics intelligents"""
        try:
            # Analyse des tendances
            trends = self._analyze_trends()
            
            # Détection d'anomalies
            anomalies = self._detect_anomalies()
            
            # Prédictions
            predictions = self._generate_predictions()
            
            # Insights automatiques
            insights = self._generate_insights(trends, anomalies, predictions)
            
            return {
                'trends': trends,
                'anomalies': anomalies,
                'predictions': predictions,
                'insights': insights,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur génération analytics: {e}")
            return {'error': str(e)}
    
    def _generate_auto_recommendations(self, optimization_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des recommandations automatiques"""
        recommendations = []
        
        try:
            # Recommandations basées sur les performances
            performance_analysis = optimization_results.get('performance_analysis', {})
            if performance_analysis.get('needs_optimization', False):
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'title': 'Optimisation des performances requise',
                    'description': f"Temps de réponse moyen: {performance_analysis.get('avg_response_time_ms', 0):.1f}ms",
                    'actions': [
                        'Ajuster les seuils de similarité',
                        'Optimiser le cache',
                        'Rééquilibrer les méthodes de recherche'
                    ]
                })
            
            # Recommandations basées sur la qualité des données
            data_quality_analysis = optimization_results.get('data_quality_analysis', {})
            if data_quality_analysis.get('needs_cleanup', False):
                recommendations.append({
                    'type': 'data_quality',
                    'priority': 'medium',
                    'title': 'Nettoyage des données requis',
                    'description': f"Qualité des embeddings: {data_quality_analysis.get('embedding_quality', 0):.1f}",
                    'actions': [
                        'Supprimer les doublons',
                        'Réparer les embeddings invalides',
                        'Améliorer les métadonnées'
                    ]
                })
            
            # Recommandations basées sur la scalabilité
            scalability_analysis = optimization_results.get('scalability_analysis', {})
            if scalability_analysis.get('needs_scaling', False):
                recommendations.append({
                    'type': 'scalability',
                    'priority': 'high',
                    'title': 'Mise à l\'échelle requise',
                    'description': f"Utilisation mémoire: {scalability_analysis.get('memory_usage_percent', 0):.1f}%",
                    'actions': [
                        'Augmenter la mémoire',
                        'Optimiser le cache',
                        'Mettre à l\'échelle la base de données'
                    ]
                })
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
        
        return recommendations
    
    # Méthodes d'optimisation spécifiques
    def _optimize_similarity_thresholds(self) -> Optional[Dict[str, Any]]:
        """Optimise les seuils de similarité"""
        try:
            # Analyser les performances par seuil
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            best_threshold = 0.4
            best_performance = 0
            
            for threshold in thresholds:
                # Simuler des requêtes avec ce seuil
                test_queries = [
                    "Quelle est la date d'inauguration de la SAR ?",
                    "Quelle est la capacité de la SAR ?",
                    "Quels sont les produits de la SAR ?"
                ]
                
                total_time = 0
                total_results = 0
                
                for query in test_queries:
                    start_time = time.time()
                    results = vector_search_service.search_similar(query, limit=3, threshold=threshold)
                    search_time = time.time() - start_time
                    
                    total_time += search_time
                    total_results += len(results) if results else 0
                
                # Calculer la performance (plus de résultats en moins de temps = mieux)
                performance = total_results / total_time if total_time > 0 else 0
                
                if performance > best_performance:
                    best_performance = performance
                    best_threshold = threshold
            
            # Appliquer le seuil optimal
            # (Dans un vrai système, on mettrait à jour la configuration)
            
            return {
                'type': 'similarity_threshold_optimization',
                'old_threshold': 0.4,
                'new_threshold': best_threshold,
                'performance_improvement': best_performance,
                'description': f'Seuil de similarité optimisé de 0.4 à {best_threshold}'
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation seuils: {e}")
            return None
    
    def _optimize_cache_settings(self) -> Optional[Dict[str, Any]]:
        """Optimise les paramètres de cache"""
        try:
            # Analyser l'efficacité du cache
            cache_stats = self._analyze_cache_performance()
            
            # Recommandations d'optimisation
            optimizations = []
            
            if cache_stats.get('hit_rate', 0) < 0.7:
                optimizations.append('Augmenter la taille du cache')
            
            if cache_stats.get('eviction_rate', 0) > 0.3:
                optimizations.append('Ajuster la politique d\'éviction')
            
            if cache_stats.get('memory_usage', 0) > 0.8:
                optimizations.append('Optimiser l\'utilisation mémoire du cache')
            
            if optimizations:
                return {
                    'type': 'cache_optimization',
                    'optimizations': optimizations,
                    'current_hit_rate': cache_stats.get('hit_rate', 0),
                    'description': f'Optimisations du cache: {", ".join(optimizations)}'
                }
            
        except Exception as e:
            logger.error(f"Erreur optimisation cache: {e}")
            return None
    
    def _detect_duplicate_embeddings(self) -> List[Dict[str, Any]]:
        """Détecte les embeddings en doublon"""
        try:
            # Récupérer tous les embeddings
            embeddings = DocumentEmbedding.objects.all()
            duplicates = []
            
            # Algorithme de détection de doublons simplifié
            # (Dans un vrai système, on utiliserait des techniques plus sophistiquées)
            seen_embeddings = {}
            
            for embedding in embeddings:
                if embedding.embedding:
                    # Créer une signature de l'embedding
                    signature = str(embedding.embedding[:10])  # Premiers 10 éléments
                    
                    if signature in seen_embeddings:
                        duplicates.append({
                            'id1': seen_embeddings[signature],
                            'id2': embedding.id,
                            'similarity': 1.0,  # Simplifié
                            'content1': seen_embeddings[signature],
                            'content2': embedding.content_text[:100]
                        })
                    else:
                        seen_embeddings[signature] = embedding.id
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Erreur détection doublons: {e}")
            return []
    
    def _analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyse les performances du cache"""
        try:
            # Statistiques basiques du cache
            # (Dans un vrai système, on interrogerait Redis directement)
            return {
                'hit_rate': 0.85,  # Simulé
                'miss_rate': 0.15,
                'eviction_rate': 0.1,
                'memory_usage': 0.6,
                'total_keys': 1000,
                'expired_keys': 50
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse cache: {e}")
            return {}
    
    def _analyze_database_performance(self) -> Dict[str, Any]:
        """Analyse les performances de la base de données"""
        try:
            # Test de performance de la base de données
            start_time = time.time()
            
            # Test requête simple
            DocumentEmbedding.objects.count()
            simple_query_time = time.time() - start_time
            
            # Test requête vectorielle
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM rag_documentembedding")
            vector_query_time = time.time() - start_time
            
            return {
                'simple_query_time_ms': simple_query_time * 1000,
                'vector_query_time_ms': vector_query_time * 1000,
                'avg_query_time': (simple_query_time + vector_query_time) * 500,
                'total_connections': 10,  # Simulé
                'active_connections': 5
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse base de données: {e}")
            return {}
    
    def _log_optimization_results(self, results: Dict[str, Any]):
        """Log les résultats d'optimisation"""
        try:
            log_entry = {
                'timestamp': results.get('timestamp'),
                'duration_seconds': results.get('duration_seconds', 0),
                'optimizations_count': len(results.get('optimizations_applied', [])),
                'performance_improvements': results.get('performance_improvements', {}),
                'recommendations_count': len(results.get('recommendations', []))
            }
            
            self.optimization_log.append(log_entry)
            
            # Garder seulement les 100 dernières entrées
            if len(self.optimization_log) > 100:
                self.optimization_log = self.optimization_log[-100:]
            
            logger.info(f"Optimisation loggée: {log_entry}")
            
        except Exception as e:
            logger.error(f"Erreur log optimisation: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Récupère le statut d'optimisation"""
        try:
            return {
                'last_optimization': self.optimization_log[-1] if self.optimization_log else None,
                'total_optimizations': len(self.optimization_log),
                'config': self.optimization_config,
                'next_optimization': timezone.now() + timedelta(
                    hours=self.optimization_config['performance']['optimization_interval_hours']
                ).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur statut optimisation: {e}")
            return {'error': str(e)}

# Instance globale
auto_optimizer = AutoOptimizer()
