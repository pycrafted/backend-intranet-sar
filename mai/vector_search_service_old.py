"""
Service de recherche vectorielle optimisé avec pgvector.
Utilise all-MiniLM-L6-v2 et PostgreSQL avec extension vector.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from .models import DocumentEmbedding, RAGSearchLog
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)

class VectorSearchService:
    """
    Service de recherche vectorielle utilisant pgvector.
    Optimisé pour all-MiniLM-L6-v2 (384D) selon les choix validés.
    """
    
    def __init__(self):
        """Initialise le service de recherche vectorielle"""
        self.embedding_service = embedding_service
        self.dimension = 384
        self.cache_ttl = getattr(settings, 'RAG_CACHE_TTL', 3600)
        self.default_threshold = getattr(settings, 'RAG_SIMILARITY_THRESHOLD', 0.7)
        self.max_results = getattr(settings, 'RAG_MAX_DOCUMENTS', 5)
        
        logger.info(f"VectorSearchService initialisé (dimension: {self.dimension})")
    
    def search_similar(self, query: str, limit: int = None, threshold: float = None, 
                      use_cache: bool = True) -> List[DocumentEmbedding]:
        """
        Recherche les documents les plus similaires à la requête.
        
        Args:
            query: Requête de recherche
            limit: Nombre maximum de résultats (défaut: RAG_MAX_DOCUMENTS)
            threshold: Seuil de similarité minimum (défaut: RAG_SIMILARITY_THRESHOLD)
            use_cache: Utiliser le cache Redis si disponible
            
        Returns:
            Liste des documents similaires triés par similarité
        """
        if not query or not query.strip():
            raise ValueError("La requête ne peut pas être vide")
        
        query = query.strip()
        limit = limit or self.max_results
        threshold = threshold or self.default_threshold
        
        # Vérifier le cache si activé
        if use_cache:
            cache_key = f"search:{hash(f'{query}:{limit}:{threshold}')}"
            cached_results = cache.get(cache_key)
            if cached_results:
                logger.debug(f"Résultats trouvés dans le cache pour: {query[:50]}...")
                return self._deserialize_cached_results(cached_results)
        
        try:
            start_time = time.time()
            
            # Générer l'embedding de la requête
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Recherche vectorielle avec pgvector
            similar_docs = self._perform_vector_search(query_embedding, limit, threshold)
            
            search_time = time.time() - start_time
            
            # Logger la recherche
            RAGSearchLog.log_search(
                query=query,
                method='vectorial',
                results_count=len(similar_docs),
                response_time_ms=search_time * 1000,
                similarity_threshold=threshold,
                success=True
            )
            
            logger.info(f"Recherche vectorielle: {len(similar_docs)} résultats en {search_time:.3f}s")
            
            # Mettre en cache si activé
            if use_cache and similar_docs:
                cache.set(cache_key, self._serialize_results(similar_docs), self.cache_ttl)
                logger.debug(f"Résultats mis en cache pour: {query[:50]}...")
            
            return similar_docs
            
        except Exception as e:
            # Logger l'erreur
            RAGSearchLog.log_search(
                query=query,
                method='vectorial',
                results_count=0,
                response_time_ms=0,
                similarity_threshold=threshold,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Erreur lors de la recherche vectorielle: {e}")
            raise RuntimeError(f"Erreur de recherche vectorielle: {e}")
    
    def _perform_vector_search(self, query_embedding: List[float], limit: int, 
                             threshold: float) -> List[DocumentEmbedding]:
        """
        Exécute la recherche vectorielle avec pgvector.
        
        Args:
            query_embedding: Embedding de la requête (384D)
            limit: Nombre maximum de résultats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des documents similaires
        """
        try:
            with connection.cursor() as cursor:
                # Requête SQL avec pgvector
                # Utilise l'opérateur <=> pour la distance cosinus
                sql = """
                    SELECT id, content_text, embedding, metadata, created_at, updated_at,
                           (1 - (embedding <=> %s)) as similarity
                    FROM rag_documentembedding
                    WHERE (1 - (embedding <=> %s)) >= %s
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """
                
                # Convertir l'embedding en type vector PostgreSQL
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                cursor.execute(sql, [
                    vector_str,       # Pour le calcul de similarité
                    vector_str,       # Pour le filtre de seuil
                    threshold,        # Seuil de similarité
                    vector_str,       # Pour l'ordre de tri
                    limit             # Limite de résultats
                ])
                
                results = []
                for row in cursor.fetchall():
                    # Créer un objet DocumentEmbedding temporaire pour les résultats
                    doc = DocumentEmbedding()
                    doc.id = row[0]
                    doc.content_text = row[1]
                    doc.embedding = row[2]
                    doc.metadata = row[3]
                    doc.created_at = row[4]
                    doc.updated_at = row[5]
                    # Ajouter la similarité calculée
                    doc.similarity = row[6]
                    results.append(doc)
                
                search_time = time.time() - start_time
                
                # Logger la recherche
                RAGSearchLog.log_search(
                    query=query,
                    method='vectorial',
                    results_count=len(results),
                    response_time_ms=int(search_time * 1000),
                    success=True
                )
                
                return results
                
        except Exception as e:
            logger.error(f"Erreur SQL lors de la recherche vectorielle: {e}")
            RAGSearchLog.log_search(
                query=query,
                method='vectorial',
                results_count=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error_message=str(e)
            )
            return []
    
    def search_by_metadata(self, query: str, metadata_filters: Dict[str, Any] = None,
                          limit: int = None, threshold: float = None) -> List[DocumentEmbedding]:
        """
        Recherche vectorielle avec filtres sur les métadonnées.
        
        Args:
            query: Requête de recherche
            metadata_filters: Filtres sur les métadonnées
            limit: Nombre maximum de résultats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des documents similaires filtrés
        """
        if not query or not query.strip():
            raise ValueError("La requête ne peut pas être vide")
        
        query = query.strip()
        limit = limit or self.max_results
        threshold = threshold or self.default_threshold
        
        try:
            start_time = time.time()
            
            # Générer l'embedding de la requête
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Construire la requête SQL avec filtres
            where_conditions = ["(1 - (embedding <=> %s)) >= %s"]
            params = [query_embedding, threshold]
            
            if metadata_filters:
                for key, value in metadata_filters.items():
                    where_conditions.append(f"metadata->>%s = %s")
                    params.extend([key, str(value)])
            
            where_clause = " AND ".join(where_conditions)
            
            with connection.cursor() as cursor:
                sql = f"""
                    SELECT id, content_text, embedding, metadata, created_at, updated_at,
                           (1 - (embedding <=> %s)) as similarity
                    FROM rag_documentembedding
                    WHERE {where_clause}
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """
                
                # Convertir l'embedding en type vector PostgreSQL
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                cursor.execute(sql, params + [vector_str, limit])
                
                results = []
                for row in cursor.fetchall():
                    doc = DocumentEmbedding(
                        id=row[0],
                        content_text=row[1],
                        embedding=row[2],
                        metadata=row[3],
                        created_at=row[4],
                        updated_at=row[5]
                    )
                    doc.similarity = row[6]
                    results.append(doc)
                
                search_time = time.time() - start_time
                
                # Logger la recherche
                RAGSearchLog.log_search(
                    query=query,
                    method='vectorial_filtered',
                    results_count=len(results),
                    response_time_ms=search_time * 1000,
                    similarity_threshold=threshold,
                    success=True
                )
                
                logger.info(f"Recherche vectorielle filtrée: {len(results)} résultats en {search_time:.3f}s")
                
                return results
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle filtrée: {e}")
            raise RuntimeError(f"Erreur de recherche vectorielle filtrée: {e}")
    
    def get_similarity_stats(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Obtient des statistiques de similarité pour une requête.
        
        Args:
            query: Requête de recherche
            limit: Nombre de résultats à analyser
            
        Returns:
            Dictionnaire avec les statistiques de similarité
        """
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            
            with connection.cursor() as cursor:
                sql = """
                    SELECT (1 - (embedding <=> %s)) as similarity
                    FROM rag_documentembedding
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """
                
                # Convertir l'embedding en type vector PostgreSQL
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                cursor.execute(sql, [vector_str, vector_str, limit])
                similarities = [row[0] for row in cursor.fetchall()]
                
                if not similarities:
                    return {
                        'count': 0,
                        'avg_similarity': 0,
                        'max_similarity': 0,
                        'min_similarity': 0
                    }
                
                return {
                    'count': len(similarities),
                    'avg_similarity': sum(similarities) / len(similarities),
                    'max_similarity': max(similarities),
                    'min_similarity': min(similarities),
                    'similarities': similarities
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return {'error': str(e)}
    
    def _serialize_results(self, results: List[DocumentEmbedding]) -> List[Dict[str, Any]]:
        """Sérialise les résultats pour le cache"""
        return [doc.to_dict() for doc in results]
    
    def _deserialize_cached_results(self, cached_data: List[Dict[str, Any]]) -> List[DocumentEmbedding]:
        """Désérialise les résultats du cache"""
        results = []
        for data in cached_data:
            doc = DocumentEmbedding(
                id=data['id'],
                content=data['content'],
                embedding=data['metadata'].get('embedding', []),
                metadata=data['metadata'],
                created_at=data['created_at'],
                updated_at=data['updated_at']
            )
            results.append(doc)
        return results
    
    def clear_search_cache(self) -> int:
        """
        Vide le cache des recherches.
        
        Returns:
            Nombre d'éléments supprimés du cache
        """
        try:
            cache.clear()
            logger.info("Cache des recherches vidé")
            return 1
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {e}")
            return 0
    
    def get_search_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Obtient les statistiques des recherches.
        
        Args:
            hours: Nombre d'heures à analyser
            
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            since = timezone.now() - timedelta(hours=hours)
            
            logs = RAGSearchLog.objects.filter(created_at__gte=since)
            
            total_searches = logs.count()
            successful_searches = logs.filter(success=True).count()
            failed_searches = logs.filter(success=False).count()
            
            if total_searches > 0:
                from django.db import models
                avg_response_time = logs.aggregate(
                    avg_time=models.Avg('response_time_ms')
                )['avg_time'] or 0
                
                avg_results = logs.aggregate(
                    avg_results=models.Avg('results_count')
                )['avg_results'] or 0
            else:
                avg_response_time = 0
                avg_results = 0
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'failed_searches': failed_searches,
                'success_rate': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
                'avg_response_time_ms': avg_response_time,
                'avg_results_count': avg_results,
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {'error': str(e)}


# Instance singleton du service
vector_search_service = VectorSearchService()
