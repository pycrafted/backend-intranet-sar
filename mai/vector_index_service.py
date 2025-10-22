"""
Service d'optimisation des index vectoriels pour la Phase 6.
Optimise les performances de recherche avec des index avancés.
"""
import time
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db import connection, transaction
from django.utils import timezone
from mai.models import DocumentEmbedding, RAGSearchLog
from mai.vector_search_service import vector_search_service
from mai.embedding_service import embedding_service
from mai.cache_service import cache_service as advanced_cache_service

logger = logging.getLogger(__name__)

class VectorIndexService:
    """Service d'optimisation des index vectoriels avancés"""
    
    def __init__(self):
        self.index_config = self._load_index_config()
        self.optimization_history = []
        
    def _load_index_config(self) -> Dict[str, Any]:
        """Charge la configuration des index"""
        return {
            'index_types': {
                'ivfflat': {
                    'lists': 100,
                    'probes': 10,
                    'description': 'Index IVFFlat pour recherche rapide'
                },
                'hnsw': {
                    'm': 16,
                    'ef_construction': 64,
                    'ef_search': 40,
                    'description': 'Index HNSW pour recherche précise'
                }
            },
            'optimization': {
                'auto_reindex_threshold': 1000,  # Reindexer après 1000 nouveaux documents
                'vacuum_interval_hours': 24,
                'analyze_interval_hours': 12,
                'parallel_workers': 4
            },
            'performance': {
                'target_query_time_ms': 100,
                'target_index_size_mb': 50,
                'compression_enabled': True,
                'memory_efficient': True
            }
        }
    
    def build_optimized_index(self, index_type: str = 'ivfflat') -> Dict[str, Any]:
        """Construit un index vectoriel optimisé"""
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                # 1. Supprimer l'ancien index s'il existe
                cursor.execute("DROP INDEX IF EXISTS rag_documentembedding_embedding_idx")
                
                # 2. Construire le nouvel index selon le type
                if index_type == 'ivfflat':
                    index_sql = f"""
                    CREATE INDEX rag_documentembedding_embedding_idx 
                    ON rag_documentembedding 
                    USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = {self.index_config['index_types']['ivfflat']['lists']})
                    """
                elif index_type == 'hnsw':
                    index_sql = f"""
                    CREATE INDEX rag_documentembedding_embedding_idx 
                    ON rag_documentembedding 
                    USING hnsw (embedding vector_cosine_ops) 
                    WITH (m = {self.index_config['index_types']['hnsw']['m']}, 
                          ef_construction = {self.index_config['index_types']['hnsw']['ef_construction']})
                    """
                else:
                    raise ValueError(f"Type d'index non supporté: {index_type}")
                
                cursor.execute(index_sql)
                
                # 3. Analyser la table pour optimiser les statistiques
                cursor.execute("ANALYZE rag_documentembedding")
                
                # 4. Vérifier la taille de l'index
                cursor.execute("""
                    SELECT pg_size_pretty(pg_relation_size('rag_documentembedding_embedding_idx')) as index_size
                """)
                index_size = cursor.fetchone()[0]
                
                duration = time.time() - start_time
                
                # Enregistrer l'optimisation
                self.optimization_history.append({
                    'timestamp': timezone.now(),
                    'type': 'index_build',
                    'index_type': index_type,
                    'duration_seconds': duration,
                    'index_size': index_size,
                    'success': True
                })
                
                return {
                    'success': True,
                    'index_type': index_type,
                    'duration_seconds': round(duration, 2),
                    'index_size': index_size,
                    'message': f'Index {index_type} construit avec succès'
                }
                
        except Exception as e:
            logger.error(f"Erreur construction index: {e}")
            duration = time.time() - start_time
            
            self.optimization_history.append({
                'timestamp': timezone.now(),
                'type': 'index_build',
                'index_type': index_type,
                'duration_seconds': duration,
                'success': False,
                'error': str(e)
            })
            
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2)
            }
    
    def optimize_existing_index(self) -> Dict[str, Any]:
        """Optimise l'index existant"""
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                # 1. VACUUM pour récupérer l'espace
                cursor.execute("VACUUM rag_documentembedding")
                
                # 2. ANALYZE pour mettre à jour les statistiques
                cursor.execute("ANALYZE rag_documentembedding")
                
                # 3. REINDEX pour reconstruire l'index
                cursor.execute("REINDEX INDEX rag_documentembedding_embedding_idx")
                
                # 4. Vérifier les statistiques de l'index
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes 
                    WHERE indexname = 'rag_documentembedding_embedding_idx'
                """)
                
                stats = cursor.fetchone()
                
                duration = time.time() - start_time
                
                self.optimization_history.append({
                    'timestamp': timezone.now(),
                    'type': 'index_optimization',
                    'duration_seconds': duration,
                    'success': True,
                    'stats': {
                        'index_size': stats[3] if stats else 'N/A',
                        'index_scans': stats[4] if stats else 0,
                        'tuples_read': stats[5] if stats else 0,
                        'tuples_fetched': stats[6] if stats else 0
                    }
                })
                
                return {
                    'success': True,
                    'duration_seconds': round(duration, 2),
                    'index_stats': {
                        'size': stats[3] if stats else 'N/A',
                        'scans': stats[4] if stats else 0,
                        'tuples_read': stats[5] if stats else 0,
                        'tuples_fetched': stats[6] if stats else 0
                    },
                    'message': 'Index optimisé avec succès'
                }
                
        except Exception as e:
            logger.error(f"Erreur optimisation index: {e}")
            duration = time.time() - start_time
            
            self.optimization_history.append({
                'timestamp': timezone.now(),
                'type': 'index_optimization',
                'duration_seconds': duration,
                'success': False,
                'error': str(e)
            })
            
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2)
            }
    
    def analyze_index_performance(self) -> Dict[str, Any]:
        """Analyse les performances de l'index"""
        try:
            with connection.cursor() as cursor:
                # 1. Statistiques de l'index
                cursor.execute("""
                    SELECT 
                        indexrelname as indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                        idx_scan as total_scans,
                        idx_tup_read as total_tuples_read,
                        idx_tup_fetch as total_tuples_fetched,
                        CASE 
                            WHEN idx_scan > 0 THEN 
                                ROUND((idx_tup_fetch::float / idx_tup_read::float) * 100, 2)
                            ELSE 0 
                        END as efficiency_percent
                    FROM pg_stat_user_indexes 
                    WHERE indexrelname = 'rag_documentembedding_embedding_idx'
                """)
                
                index_stats = cursor.fetchone()
                
                # 2. Statistiques de la table
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('rag_documentembedding')) as table_size,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables 
                    WHERE relname = 'rag_documentembedding'
                """)
                
                table_stats = cursor.fetchone()
                
                # 3. Test de performance de recherche
                test_queries = [
                    "Quelle est la date d'inauguration de la SAR ?",
                    "Quelle est la capacité de la SAR ?",
                    "Quels sont les produits de la SAR ?"
                ]
                
                search_times = []
                for query in test_queries:
                    start_time = time.time()
                    embedding = embedding_service.generate_embedding(query)
                    
                    cursor.execute("""
                        SELECT id, content_text, metadata, 
                               embedding <=> %s as distance
                        FROM rag_documentembedding
                        ORDER BY embedding <=> %s
                        LIMIT 5
                    """, [embedding, embedding])
                    
                    results = cursor.fetchall()
                    search_time = (time.time() - start_time) * 1000  # en ms
                    search_times.append(search_time)
                
                avg_search_time = sum(search_times) / len(search_times)
                
                # 4. Calculer le score de performance
                performance_score = 100
                if avg_search_time > self.index_config['performance']['target_query_time_ms']:
                    performance_score -= min(50, (avg_search_time - self.index_config['performance']['target_query_time_ms']) * 2)
                
                if index_stats and index_stats[4] > 0:  # tuples_read
                    efficiency = index_stats[5] / index_stats[4] if index_stats[4] > 0 else 0
                    if efficiency < 0.8:
                        performance_score -= 20
                
                return {
                    'success': True,
                    'index_stats': {
                        'name': index_stats[0] if index_stats else 'N/A',
                        'size': index_stats[1] if index_stats else 'N/A',
                        'total_scans': index_stats[2] if index_stats else 0,
                        'total_tuples_read': index_stats[3] if index_stats else 0,
                        'total_tuples_fetched': index_stats[4] if index_stats else 0,
                        'efficiency_percent': index_stats[5] if index_stats else 0
                    },
                    'table_stats': {
                        'size': table_stats[0] if table_stats else 'N/A',
                        'inserts': table_stats[1] if table_stats else 0,
                        'updates': table_stats[2] if table_stats else 0,
                        'deletes': table_stats[3] if table_stats else 0,
                        'live_tuples': table_stats[4] if table_stats else 0,
                        'dead_tuples': table_stats[5] if table_stats else 0
                    },
                    'performance': {
                        'avg_search_time_ms': round(avg_search_time, 2),
                        'target_time_ms': self.index_config['performance']['target_query_time_ms'],
                        'performance_score': max(0, min(100, performance_score)),
                        'search_times': [round(t, 2) for t in search_times]
                    },
                    'recommendations': self._generate_performance_recommendations(avg_search_time, performance_score)
                }
                
        except Exception as e:
            logger.error(f"Erreur analyse performance index: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_performance_recommendations(self, avg_search_time: float, performance_score: float) -> List[str]:
        """Génère des recommandations d'optimisation"""
        recommendations = []
        
        if avg_search_time > self.index_config['performance']['target_query_time_ms']:
            recommendations.append("Considérer reconstruire l'index avec des paramètres optimisés")
            recommendations.append("Augmenter le nombre de listes pour l'index IVFFlat")
        
        if performance_score < 70:
            recommendations.append("Exécuter VACUUM ANALYZE sur la table")
            recommendations.append("Considérer partitionner la table par date")
        
        if performance_score < 50:
            recommendations.append("Reconstruire complètement l'index")
            recommendations.append("Vérifier la configuration PostgreSQL")
        
        if not recommendations:
            recommendations.append("Performance de l'index excellente")
        
        return recommendations
    
    def reindex_if_needed(self) -> Dict[str, Any]:
        """Reindexe si nécessaire basé sur les statistiques"""
        try:
            # Vérifier le nombre de nouveaux documents depuis la dernière optimisation
            last_optimization = None
            for opt in reversed(self.optimization_history):
                if opt['type'] == 'index_optimization' and opt['success']:
                    last_optimization = opt['timestamp']
                    break
            
            if last_optimization:
                new_docs = DocumentEmbedding.objects.filter(
                    created_at__gt=last_optimization
                ).count()
            else:
                new_docs = DocumentEmbedding.objects.count()
            
            threshold = self.index_config['optimization']['auto_reindex_threshold']
            
            if new_docs >= threshold:
                logger.info(f"Reindexation nécessaire: {new_docs} nouveaux documents (seuil: {threshold})")
                return self.optimize_existing_index()
            else:
                return {
                    'success': True,
                    'message': f'Reindexation non nécessaire ({new_docs}/{threshold} documents)',
                    'new_documents': new_docs,
                    'threshold': threshold
                }
                
        except Exception as e:
            logger.error(f"Erreur vérification reindexation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_index_health(self) -> Dict[str, Any]:
        """Vérifie la santé de l'index"""
        try:
            with connection.cursor() as cursor:
                # Vérifier si l'index existe
                cursor.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes 
                    WHERE tablename = 'rag_documentembedding' 
                    AND indexname = 'rag_documentembedding_embedding_idx'
                """)
                
                index_info = cursor.fetchone()
                
                if not index_info:
                    return {
                        'status': 'missing',
                        'message': 'Index vectoriel manquant',
                        'recommendations': ['Construire un nouvel index vectoriel']
                    }
                
                # Vérifier les statistiques de l'index
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_relation_size('rag_documentembedding_embedding_idx')) as size,
                        idx_scan as scans,
                        idx_tup_read as tuples_read
                    FROM pg_stat_user_indexes 
                    WHERE indexname = 'rag_documentembedding_embedding_idx'
                """)
                
                stats = cursor.fetchone()
                
                # Vérifier l'utilisation de l'index
                if stats and stats[1] == 0:  # Aucun scan
                    return {
                        'status': 'unused',
                        'message': 'Index non utilisé',
                        'size': stats[0] if stats else 'N/A',
                        'recommendations': ['Vérifier les requêtes de recherche', 'Tester les performances']
                    }
                
                # Vérifier la fragmentation
                cursor.execute("""
                    SELECT 
                        schemaname, tablename, 
                        n_dead_tup, n_live_tup,
                        ROUND((n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0)) * 100, 2) as fragmentation_percent
                    FROM pg_stat_user_tables 
                    WHERE relname = 'rag_documentembedding'
                """)
                
                frag_stats = cursor.fetchone()
                fragmentation = frag_stats[4] if frag_stats else 0
                
                if fragmentation > 20:
                    status = 'fragmented'
                    message = f'Index fragmenté ({fragmentation}%)'
                    recommendations = ['Exécuter VACUUM', 'Reconstruire l\'index']
                elif fragmentation > 10:
                    status = 'warning'
                    message = f'Index légèrement fragmenté ({fragmentation}%)'
                    recommendations = ['Surveiller la fragmentation', 'Planifier VACUUM']
                else:
                    status = 'healthy'
                    message = 'Index en bonne santé'
                    recommendations = ['Continuer la surveillance']
                
                return {
                    'status': status,
                    'message': message,
                    'size': stats[0] if stats else 'N/A',
                    'scans': stats[1] if stats else 0,
                    'tuples_read': stats[2] if stats else 0,
                    'fragmentation_percent': fragmentation,
                    'recommendations': recommendations
                }
                
        except Exception as e:
            logger.error(f"Erreur health check index: {e}")
            return {
                'status': 'error',
                'message': f'Erreur: {e}',
                'recommendations': ['Vérifier la configuration de la base de données']
            }
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des optimisations"""
        return sorted(
            self.optimization_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:50]  # 50 dernières optimisations
    
    def clear_optimization_history(self) -> bool:
        """Vide l'historique des optimisations"""
        try:
            self.optimization_history.clear()
            return True
        except Exception as e:
            logger.error(f"Erreur clear history: {e}")
            return False

# Instance globale
vector_index_service = VectorIndexService()
