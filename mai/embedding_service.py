"""
Service d'embedding optimisé pour all-MiniLM-L6-v2.
Configuration selon les choix validés : performance optimale.
"""
import logging
import time
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from django.conf import settings
from django.core.cache import cache
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service d'embedding utilisant all-MiniLM-L6-v2 (384D, rapide).
    Optimisé pour la performance selon les choix validés.
    """
    
    def __init__(self):
        """Initialise le service avec all-MiniLM-L6-v2"""
        self.model_name = 'all-MiniLM-L6-v2'
        self.dimension = 384
        self.cache_ttl = getattr(settings, 'RAG_CACHE_TTL', 3600)
        self.batch_size = getattr(settings, 'RAG_BATCH_SIZE', 50)
        
        # Charger le modèle (lazy loading)
        self._model = None
        self._model_loaded = False
        
        logger.info(f"EmbeddingService initialisé avec {self.model_name} ({self.dimension}D)")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading du modèle SentenceTransformer"""
        if not self._model_loaded:
            try:
                logger.info(f"Chargement du modèle {self.model_name}...")
                start_time = time.time()
                
                self._model = SentenceTransformer(self.model_name)
                self._model_loaded = True
                
                load_time = time.time() - start_time
                logger.info(f"Modèle {self.model_name} chargé en {load_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle {self.model_name}: {e}")
                raise RuntimeError(f"Impossible de charger le modèle {self.model_name}: {e}")
        
        return self._model
    
    def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Génère un embedding 384D optimisé pour la performance.
        
        Args:
            text: Texte à vectoriser
            use_cache: Utiliser le cache Redis si disponible
            
        Returns:
            Liste de 384 floats représentant l'embedding
        """
        if not text or not text.strip():
            raise ValueError("Le texte ne peut pas être vide")
        
        text = text.strip()
        
        # Vérifier le cache si activé
        if use_cache:
            cache_key = f"embedding:{hash(text)}"
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                logger.debug(f"Embedding trouvé dans le cache pour: {text[:50]}...")
                return cached_embedding
        
        try:
            start_time = time.time()
            
            # Générer l'embedding avec paramètres optimisés
            embedding = self.model.encode(
                text, 
                convert_to_tensor=False,
                normalize_embeddings=True,  # Normalisation pour de meilleures performances
                show_progress_bar=False,    # Désactiver la barre de progression
                batch_size=1               # Batch size optimisé
            )
            embedding_list = embedding.tolist()
            
            generation_time = time.time() - start_time
            logger.debug(f"Embedding généré en {generation_time:.3f}s pour: {text[:50]}...")
            
            # Valider la dimension
            if len(embedding_list) != self.dimension:
                raise ValueError(f"Dimension incorrecte: {len(embedding_list)} au lieu de {self.dimension}")
            
            # Mettre en cache si activé
            if use_cache:
                cache.set(cache_key, embedding_list, self.cache_ttl)
                logger.debug(f"Embedding mis en cache pour: {text[:50]}...")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embedding: {e}")
            raise RuntimeError(f"Impossible de générer l'embedding: {e}")
    
    def generate_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Génère des embeddings par batch pour optimiser les performances.
        
        Args:
            texts: Liste des textes à vectoriser
            use_cache: Utiliser le cache Redis si disponible
            
        Returns:
            Liste de listes d'embeddings (384D chacun)
        """
        if not texts:
            return []
        
        # Filtrer les textes vides
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("Aucun texte valide fourni")
        
        logger.info(f"Génération de {len(valid_texts)} embeddings par batch...")
        
        try:
            start_time = time.time()
            
            # Générer les embeddings par batch
            embeddings = self.model.encode(valid_texts, convert_to_tensor=False, batch_size=self.batch_size)
            embeddings_list = embeddings.tolist()
            
            generation_time = time.time() - start_time
            logger.info(f"{len(embeddings_list)} embeddings générés en {generation_time:.2f}s "
                       f"({generation_time/len(embeddings_list)*1000:.1f}ms par embedding)")
            
            # Valider les dimensions
            for i, embedding in enumerate(embeddings_list):
                if len(embedding) != self.dimension:
                    raise ValueError(f"Dimension incorrecte pour l'embedding {i}: "
                                   f"{len(embedding)} au lieu de {self.dimension}")
            
            # Mettre en cache si activé
            if use_cache:
                for text, embedding in zip(valid_texts, embeddings_list):
                    cache_key = f"embedding:{hash(text)}"
                    cache.set(cache_key, embedding, self.cache_ttl)
                
                logger.debug(f"{len(embeddings_list)} embeddings mis en cache")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embeddings par batch: {e}")
            raise RuntimeError(f"Impossible de générer les embeddings: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retourne les informations du modèle sélectionné.
        
        Returns:
            Dictionnaire avec les informations du modèle
        """
        return {
            'name': self.model_name,
            'dimension': self.dimension,
            'type': 'sentence-transformers',
            'optimized_for': 'performance',
            'loaded': self._model_loaded,
            'cache_enabled': True,
            'cache_ttl': self.cache_ttl,
            'batch_size': self.batch_size
        }
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Valide qu'un embedding est correct.
        
        Args:
            embedding: Embedding à valider
            
        Returns:
            True si l'embedding est valide
        """
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) != self.dimension:
            return False
        
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        
        # Vérifier qu'il n'y a pas de NaN ou Inf
        try:
            np_embedding = np.array(embedding)
            if np.any(np.isnan(np_embedding)) or np.any(np.isinf(np_embedding)):
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def clear_cache(self) -> int:
        """
        Vide le cache des embeddings.
        
        Returns:
            Nombre d'éléments supprimés du cache
        """
        try:
            # Utiliser un pattern pour supprimer tous les embeddings du cache
            # Note: Cette implémentation dépend du backend de cache utilisé
            cache.clear()
            logger.info("Cache des embeddings vidé")
            return 1  # Indique que l'opération a réussi
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache.
        
        Returns:
            Dictionnaire avec les statistiques du cache
        """
        try:
            # Cette implémentation dépend du backend de cache
            # Pour Redis, on pourrait utiliser des commandes spécifiques
            return {
                'cache_backend': str(type(cache).__name__),
                'cache_ttl': self.cache_ttl,
                'model_name': self.model_name,
                'dimension': self.dimension
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats du cache: {e}")
            return {'error': str(e)}


# Instance singleton du service
embedding_service = EmbeddingService()
