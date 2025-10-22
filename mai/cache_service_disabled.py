"""
Service de cache local pour la Phase 6 (Redis complètement désactivé en production).
Utilise uniquement le cache local Django pour éviter toute dépendance Redis.
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
    """Service de cache local avec optimisations intelligentes (Redis complètement désactivé)"""
    
    def __init__(self):
        self.redis_client = None  # Redis complètement désactivé
        self.cache_config = self._load_cache_config()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
    def _initialize_redis(self):
        """Redis complètement désactivé en production"""
        logger.info("Redis complètement désactivé en production - utilisation du cache local uniquement")
        return None
        
    def _load_cache_config(self) -> Dict[str, Any]:
        """Charge la configuration du cache local"""
        return {
            'key_prefix': 'sar_rag_local',
            'embedding_ttl': 3600,  # 1 heure
            'search_ttl': 1800,     # 30 minutes
            'context_ttl': 900,     # 15 minutes
            'stats_ttl': 300,       # 5 minutes
            'max_memory_usage': 0.8,
            'eviction_policy': 'lru',
            'compression_enabled': True,
            'redis_enabled': False,  # Redis désactivé
        }
    
    def get_embedding_cache(self, text: str) -> Optional[List[float]]:
        """Récupère un embedding depuis le cache local (Redis désactivé)"""
        if not self._is_cache_enabled():
            return None
            
        try:
            key = f"{self.cache_config['key_prefix']}:embedding:{hashlib.md5(text.encode()).hexdigest()}"
            cached_data = cache.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache hit pour embedding: {text[:50]}...")
                return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération cache embedding: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set_embedding_cache(self, text: str, embedding: List[float]) -> bool:
        """Met en cache un embedding dans le cache local (Redis désactivé)"""
        if not self._is_cache_enabled():
            return False
            
        try:
            key = f"{self.cache_config['key_prefix']}:embedding:{hashlib.md5(text.encode()).hexdigest()}"
            data = json.dumps(embedding)
            
            cache.set(key, data, self.cache_config['embedding_ttl'])
            self.cache_stats['sets'] += 1
            logger.debug(f"Embedding mis en cache: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise en cache embedding: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_search_cache(self, query: str, filters: Dict = None) -> Optional[Dict]:
        """Récupère un résultat de recherche depuis le cache local"""
        if not self._is_cache_enabled():
            return None
            
        try:
            cache_key = self._generate_search_key(query, filters)
            cached_data = cache.get(cache_key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache hit pour recherche: {query[:50]}...")
                return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération cache recherche: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set_search_cache(self, query: str, results: Dict, filters: Dict = None) -> bool:
        """Met en cache un résultat de recherche dans le cache local"""
        if not self._is_cache_enabled():
            return False
            
        try:
            cache_key = self._generate_search_key(query, filters)
            data = json.dumps(results)
            
            cache.set(cache_key, data, self.cache_config['search_ttl'])
            self.cache_stats['sets'] += 1
            logger.debug(f"Résultat de recherche mis en cache: {query[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise en cache recherche: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_context_cache(self, context_id: str) -> Optional[str]:
        """Récupère un contexte depuis le cache local"""
        if not self._is_cache_enabled():
            return None
            
        try:
            key = f"{self.cache_config['key_prefix']}:context:{context_id}"
            cached_data = cache.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                return cached_data
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération cache contexte: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set_context_cache(self, context_id: str, context: str) -> bool:
        """Met en cache un contexte dans le cache local"""
        if not self._is_cache_enabled():
            return False
            
        try:
            key = f"{self.cache_config['key_prefix']}:context:{context_id}"
            cache.set(key, context, self.cache_config['context_ttl'])
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise en cache contexte: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_stats_cache(self, stats_type: str) -> Optional[Dict]:
        """Récupère des statistiques depuis le cache local"""
        if not self._is_cache_enabled():
            return None
            
        try:
            key = f"{self.cache_config['key_prefix']}:stats:{stats_type}"
            cached_data = cache.get(key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                return json.loads(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération cache stats: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set_stats_cache(self, stats_type: str, data: Dict) -> bool:
        """Met en cache des statistiques dans le cache local"""
        if not self._is_cache_enabled():
            return False
            
        try:
            key = f"{self.cache_config['key_prefix']}:stats:{stats_type}"
            cache.set(key, json.dumps(data), self.cache_config['stats_ttl'])
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise en cache stats: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def clear_cache(self, pattern: str = None) -> bool:
        """Vide le cache local (Redis désactivé)"""
        try:
            if pattern:
                # Pour le cache local, on ne peut pas filtrer par pattern
                logger.warning("Filtrage par pattern non supporté avec le cache local")
            
            cache.clear()
            self.cache_stats['deletes'] += 1
            logger.info("Cache local vidé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur vidage cache: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache local"""
        try:
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_type': 'local_django',
                'redis_enabled': False,
                'redis_available': False,
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'sets': self.cache_stats['sets'],
                'deletes': self.cache_stats['deletes'],
                'errors': self.cache_stats['errors'],
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests,
                'memory_usage': 'N/A (cache local)',
                'connected_clients': 0,
                'total_commands': 0,
                'keyspace_hits': 0,
                'keyspace_misses': 0
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération stats cache: {e}")
            return {
                'cache_type': 'local_django',
                'redis_enabled': False,
                'redis_available': False,
                'error': str(e)
            }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimise le cache local (Redis désactivé)"""
        try:
            logger.info("Optimisation du cache local...")
            
            # Pour le cache local, on ne peut pas faire grand-chose
            # On peut juste nettoyer les clés expirées
            cache.clear()
            
            return {
                'success': True,
                'message': 'Cache local optimisé (Redis désactivé)',
                'optimizations': [
                    'Cache local vidé',
                    'Clés expirées supprimées'
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation cache: {e}")
            return {
                'success': False,
                'message': f'Erreur optimisation cache: {e}',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du cache local"""
        try:
            # Test simple du cache local
            test_key = f"{self.cache_config['key_prefix']}:health_check"
            test_value = "test_value"
            
            # Test d'écriture
            cache.set(test_key, test_value, 60)
            
            # Test de lecture
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                return {
                    'status': 'healthy',
                    'cache_type': 'local_django',
                    'redis_enabled': False,
                    'redis_available': False,
                    'message': 'Cache local fonctionne correctement',
                    'recommendations': []
                }
            else:
                return {
                    'status': 'unhealthy',
                    'cache_type': 'local_django',
                    'redis_enabled': False,
                    'redis_available': False,
                    'message': 'Cache local ne fonctionne pas correctement',
                    'recommendations': ['Vérifier la configuration du cache Django']
                }
                
        except Exception as e:
            logger.error(f"Erreur health check cache: {e}")
            return {
                'status': 'error',
                'cache_type': 'local_django',
                'redis_enabled': False,
                'redis_available': False,
                'message': f'Erreur health check: {e}',
                'recommendations': ['Vérifier la configuration du cache Django']
            }
    
    def _is_cache_enabled(self) -> bool:
        """Vérifie si le cache est activé"""
        return getattr(settings, 'RAG_CONFIG', {}).get('CACHE_ENABLED', False)
    
    def _generate_search_key(self, query: str, filters: Dict = None) -> str:
        """Génère une clé de cache pour une recherche"""
        key_data = {
            'query': query,
            'filters': filters or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"{self.cache_config['key_prefix']}:search:{hashlib.md5(key_string.encode()).hexdigest()}"

# Instance globale du service de cache
cache_service = AdvancedCacheService()
