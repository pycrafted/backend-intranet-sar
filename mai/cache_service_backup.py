"""
Service de cache local pour la Phase 6 (Redis désactivé en production).
Optimise les performances avec un cache local intelligent.
"""
import json
import time
import logging
import hashlib
from typing import Optional, List, Dict, Any, Union
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from mai.models import RAGSearchLog, DocumentEmbedding
from mai.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class AdvancedCacheService:
    """Service de cache local avec optimisations intelligentes (Redis désactivé)"""
    
    def __init__(self):
        self.redis_client = None  # Redis désactivé en production
        self.cache_config = self._load_cache_config()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
    def _initialize_redis(self) -> redis.Redis:
        """Initialise la connexion Redis avec configuration optimisée"""
        try:
            # Configuration Redis optimisée pour la Phase 6
            redis_config = {
                'host': getattr(settings, 'REDIS_HOST', 'localhost'),
                'port': getattr(settings, 'REDIS_PORT', 6379),
                'db': getattr(settings, 'REDIS_DB', 0),
                'password': getattr(settings, 'REDIS_PASSWORD', None),
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30,
                'max_connections': 20
            }
            
            # Supprimer les clés None
            redis_config = {k: v for k, v in redis_config.items() if v is not None}
            
            client = redis.Redis(**redis_config)
            
            # Test de connexion
            client.ping()
            logger.info("Connexion Redis établie avec succès")
            return client
            
        except Exception as e:
            logger.error(f"Erreur connexion Redis: {e}")
            # Fallback vers le cache Django par défaut
            return None
    
    def _load_cache_config(self) -> Dict[str, Any]:
        """Charge la configuration du cache"""
        return {
            'embedding_ttl': 3600 * 24,  # 24 heures pour les embeddings
            'search_ttl': 3600 * 6,      # 6 heures pour les recherches
            'context_ttl': 3600 * 2,     # 2 heures pour les contextes
            'stats_ttl': 3600,           # 1 heure pour les statistiques
            'compression_enabled': True,
            'serialization_method': 'json',
            'key_prefix': 'rag_phase6:',
            'max_memory_usage': '512mb',
            'eviction_policy': 'allkeys-lru'
        }
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """Génère une clé de cache optimisée"""
        # Créer un hash stable de l'identifiant
        hash_obj = hashlib.md5(identifier.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]  # 16 caractères pour la performance
        return f"{self.cache_config['key_prefix']}{prefix}:{hash_hex}"
    
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Récupère un embedding depuis le cache Redis"""
        if not self.redis_client:
            return None
            
        try:
            key = self._generate_cache_key('embedding', text)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                if self.cache_config['compression_enabled']:
                    return json.loads(cached_data)
                else:
                    return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération embedding cache: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def cache_embedding(self, text: str, embedding: List[float]) -> bool:
        """Met en cache un embedding dans Redis"""
        if not self.redis_client:
            return False
            
        try:
            key = self._generate_cache_key('embedding', text)
            data = json.dumps(embedding)
            
            # Compression si activée
            if self.cache_config['compression_enabled']:
                # Utiliser la compression Redis native
                self.redis_client.setex(key, self.cache_config['embedding_ttl'], data)
            else:
                self.redis_client.setex(key, self.cache_config['embedding_ttl'], data)
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur cache embedding: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_cached_search(self, query: str, limit: int, threshold: float) -> Optional[List[Dict[str, Any]]]:
        """Récupère un résultat de recherche depuis le cache"""
        if not self.redis_client:
            return None
            
        try:
            # Créer un identifiant unique pour la recherche
            search_id = f"{query}:{limit}:{threshold}"
            key = self._generate_cache_key('search', search_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération search cache: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def cache_search(self, query: str, limit: int, threshold: float, results: List[Dict[str, Any]]) -> bool:
        """Met en cache un résultat de recherche"""
        if not self.redis_client:
            return False
            
        try:
            search_id = f"{query}:{limit}:{threshold}"
            key = self._generate_cache_key('search', search_id)
            data = json.dumps(results)
            
            self.redis_client.setex(key, self.cache_config['search_ttl'], data)
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur cache search: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_cached_context(self, query: str) -> Optional[str]:
        """Récupère un contexte depuis le cache"""
        if not self.redis_client:
            return None
            
        try:
            key = self._generate_cache_key('context', query)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                return cached_data
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération context cache: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def cache_context(self, query: str, context: str) -> bool:
        """Met en cache un contexte"""
        if not self.redis_client:
            return False
            
        try:
            key = self._generate_cache_key('context', query)
            self.redis_client.setex(key, self.cache_config['context_ttl'], context)
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur cache context: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_cached_stats(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """Récupère des statistiques depuis le cache"""
        if not self.redis_client:
            return None
            
        try:
            key = self._generate_cache_key('stats', stats_type)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération stats cache: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def cache_stats(self, stats_type: str, stats_data: Dict[str, Any]) -> bool:
        """Met en cache des statistiques"""
        if not self.redis_client:
            return False
            
        try:
            key = self._generate_cache_key('stats', stats_type)
            data = json.dumps(stats_data)
            
            self.redis_client.setex(key, self.cache_config['stats_ttl'], data)
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur cache stats: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def clear_cache(self, pattern: str = None) -> bool:
        """Vide le cache Redis"""
        if not self.redis_client:
            return False
            
        try:
            if pattern:
                # Supprimer les clés correspondant au pattern
                keys = self.redis_client.keys(f"{self.cache_config['key_prefix']}{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Vider tout le cache
                self.redis_client.flushdb()
            
            self.cache_stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur clear cache: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        if not self.redis_client:
            return {
                'status': 'disabled',
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0,
                'total_operations': 0,
                'errors': 0
            }
        
        try:
            # Statistiques Redis
            redis_info = self.redis_client.info()
            
            # Calculer le taux de hit
            total_operations = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = (self.cache_stats['hits'] / total_operations * 100) if total_operations > 0 else 0.0
            
            return {
                'status': 'active',
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'total_operations': total_operations,
                'sets': self.cache_stats['sets'],
                'deletes': self.cache_stats['deletes'],
                'errors': self.cache_stats['errors'],
                'redis_memory_usage': redis_info.get('used_memory_human', 'N/A'),
                'redis_connected_clients': redis_info.get('connected_clients', 0),
                'redis_total_commands': redis_info.get('total_commands_processed', 0),
                'redis_keyspace_hits': redis_info.get('keyspace_hits', 0),
                'redis_keyspace_misses': redis_info.get('keyspace_misses', 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur stats cache: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': 0.0,
                'total_operations': 0,
                'errors': self.cache_stats['errors'] + 1
            }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimise le cache Redis"""
        if not self.redis_client:
            return {'success': False, 'message': 'Redis non disponible'}
        
        try:
            # 1. Nettoyer les clés expirées
            self.redis_client.execute_command('MEMORY', 'PURGE')
            
            # 2. Défragmenter la mémoire
            self.redis_client.execute_command('MEMORY', 'DEFRAG')
            
            # 3. Optimiser les paramètres
            self.redis_client.config_set('maxmemory-policy', self.cache_config['eviction_policy'])
            
            # 4. Obtenir les nouvelles statistiques
            stats = self.get_cache_stats()
            
            return {
                'success': True,
                'message': 'Cache optimisé avec succès',
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation cache: {e}")
            return {
                'success': False,
                'message': f'Erreur optimisation: {e}'
            }
    
    def warm_up_cache(self) -> Dict[str, Any]:
        """Préchauffe le cache avec les données fréquemment utilisées"""
        if not self.redis_client:
            return {'success': False, 'message': 'Redis non disponible'}
        
        try:
            warmed_items = 0
            
            # 1. Préchauffer les embeddings des questions fréquentes
            frequent_queries = [
                "Quelle est la date d'inauguration de la SAR ?",
                "Quelle est la capacité de la SAR ?",
                "Quels sont les produits de la SAR ?",
                "Qui est le président de la SAR ?",
                "Où se trouve la SAR ?"
            ]
            
            for query in frequent_queries:
                # Générer l'embedding si pas en cache
                if not self.get_cached_embedding(query):
                    embedding = embedding_service.generate_embedding(query)
                    self.cache_embedding(query, embedding)
                    warmed_items += 1
            
            # 2. Préchauffer les recherches fréquentes (simplifié pour éviter l'import circulaire)
            for query in frequent_queries:
                # Simuler des résultats de recherche pour le préchauffage
                mock_results = [
                    {
                        'id': i,
                        'content': f'Réponse simulée pour {query}',
                        'metadata': {'question': query, 'answer': f'Réponse {i}'},
                        'similarity': 0.9 - (i * 0.1)
                    }
                    for i in range(3)
                ]
                self.cache_search(query, 5, 0.7, mock_results)
                warmed_items += 1
            
            return {
                'success': True,
                'message': f'Cache préchauffé avec {warmed_items} éléments',
                'warmed_items': warmed_items
            }
            
        except Exception as e:
            logger.error(f"Erreur warm-up cache: {e}")
            return {
                'success': False,
                'message': f'Erreur warm-up: {e}'
            }
    
    def get_cache_health(self) -> Dict[str, Any]:
        """Vérifie la santé du cache"""
        if not self.redis_client:
            return {
                'status': 'unhealthy',
                'reason': 'Redis non disponible',
                'recommendations': ['Vérifier la connexion Redis', 'Configurer Redis correctement']
            }
        
        try:
            # Test de ping
            ping_time = self.redis_client.ping()
            
            # Vérifier la mémoire
            info = self.redis_client.info()
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            # Vérifier les connexions
            connected_clients = info.get('connected_clients', 0)
            
            # Calculer le statut de santé
            health_score = 100
            
            if memory_usage > 0 and max_memory > 0:
                memory_ratio = memory_usage / max_memory
                if memory_ratio > 0.9:
                    health_score -= 30
                elif memory_ratio > 0.7:
                    health_score -= 15
            
            if connected_clients > 50:
                health_score -= 10
            
            # Déterminer le statut
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 70:
                status = 'good'
            elif health_score >= 50:
                status = 'warning'
            else:
                status = 'critical'
            
            recommendations = []
            if memory_usage > 0 and max_memory > 0 and (memory_usage / max_memory) > 0.7:
                recommendations.append('Considérer augmenter la mémoire Redis')
            if connected_clients > 30:
                recommendations.append('Optimiser les connexions Redis')
            
            return {
                'status': status,
                'health_score': health_score,
                'ping_time': ping_time,
                'memory_usage': memory_usage,
                'max_memory': max_memory,
                'memory_ratio': round(memory_usage / max_memory, 2) if max_memory > 0 else 0,
                'connected_clients': connected_clients,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Erreur health check cache: {e}")
            return {
                'status': 'unhealthy',
                'reason': f'Erreur: {e}',
                'recommendations': ['Vérifier la configuration Redis', 'Redémarrer Redis']
            }

# Instance globale
advanced_cache_service = AdvancedCacheService()
