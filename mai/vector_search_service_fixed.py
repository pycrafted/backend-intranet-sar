import time
import logging
from typing import List, Dict, Any, Optional
from django.db import connection
from django.conf import settings
from mai.models import DocumentEmbedding, RAGSearchLog
from mai.embedding_service import embedding_service
import json

logger = logging.getLogger(__name__)

class VectorSearchService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorSearchService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise le service de recherche vectorielle."""
        self.embedding_service = embedding_service
        self.dimension = self.embedding_service.dimension
        self.default_threshold = getattr(settings, 'RAG_SIMILARITY_THRESHOLD', 0.4)
        self.max_results = getattr(settings, 'RAG_MAX_DOCUMENTS', 5)
        logger.info(f"VectorSearchService initialisé. Dimension: {self.dimension}, Seuil: {self.default_threshold}")

    def search_similar(self, query: str, limit: int = 5, threshold: Optional[float] = None) -> List[DocumentEmbedding]:
        """
        Recherche les documents les plus similaires à la requête donnée en utilisant pgvector.
        
        Args:
            query (str): La requête de l'utilisateur.
            limit (int): Le nombre maximum de documents à retourner.
            threshold (float, optional): Le seuil de similarité. Si None, utilise le seuil par défaut.
        
        Returns:
            List[DocumentEmbedding]: Une liste de documents similaires, triés par similarité décroissante.
        """
        start_time = time.time()
        
        if threshold is None:
            threshold = self.default_threshold

        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            
            with connection.cursor() as cursor:
                # Requête SQL avec pgvector
                # Utilise l'opérateur <=> pour la distance cosinus
                sql = """
                    SELECT id, content_text, embedding, metadata, created_at, updated_at,
                           (1 - (embedding <=> %s::vector)) as similarity
                    FROM rag_documentembedding
                    WHERE (1 - (embedding <=> %s::vector)) >= %s
                    ORDER BY embedding <=> %s::vector
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

    def search_similar_with_filters(self, query: str, filters: Dict[str, Any], limit: int = 5, threshold: Optional[float] = None) -> List[DocumentEmbedding]:
        """
        Recherche les documents les plus similaires avec des filtres sur les métadonnées.
        """
        start_time = time.time()
        
        if threshold is None:
            threshold = self.default_threshold

        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            
            params = [query_embedding]
            where_conditions = ["(1 - (embedding <=> %s::vector)) >= %s"]
            params.append(threshold)
            
            for key, value in filters.items():
                where_conditions.append(f"metadata->>%s = %s")
                params.extend([key, str(value)])
            
            where_clause = " AND ".join(where_conditions)
            
            with connection.cursor() as cursor:
                sql = f"""
                    SELECT id, content_text, embedding, metadata, created_at, updated_at,
                           (1 - (embedding <=> %s::vector)) as similarity
                    FROM rag_documentembedding
                    WHERE {where_clause}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                
                # Convertir l'embedding en type vector PostgreSQL
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                cursor.execute(sql, params + [vector_str, limit])
                
                results = []
                for row in cursor.fetchall():
                    doc = DocumentEmbedding()
                    doc.id = row[0]
                    doc.content_text = row[1]
                    doc.embedding = row[2]
                    doc.metadata = row[3]
                    doc.created_at = row[4]
                    doc.updated_at = row[5]
                    doc.similarity = row[6]
                    results.append(doc)
                
                search_time = time.time() - start_time
                
                # Logger la recherche
                RAGSearchLog.log_search(
                    query=query,
                    method='vectorial_filtered',
                    results_count=len(results),
                    response_time_ms=int(search_time * 1000),
                    success=True
                )
                
                return results
                
        except Exception as e:
            logger.error(f"Erreur SQL lors de la recherche vectorielle avec filtres: {e}")
            RAGSearchLog.log_search(
                query=query,
                method='vectorial_filtered',
                results_count=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error_message=str(e)
            )
            return []

    def get_search_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Récupère les statistiques de recherche pour une période donnée.
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db import models
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        logs = RAGSearchLog.objects.filter(timestamp__range=(start_time, end_time))
        
        total_searches = logs.count()
        successful_searches = logs.filter(success=True).count()
        failed_searches = logs.filter(success=False).count()
        
        if total_searches > 0:
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
            'avg_results_per_search': avg_results,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }

vector_search_service = VectorSearchService()
