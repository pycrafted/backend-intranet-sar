from django.db import models
from django.contrib.postgres.indexes import GinIndex
import json

class DocumentEmbedding(models.Model):
    """
    Modèle pour stocker les embeddings vectoriels des documents SAR.
    Optimisé pour all-MiniLM-L6-v2 (384 dimensions).
    """
    content_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type de contenu"
    )
    content_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="ID du contenu"
    )
    content_text = models.TextField(
        help_text="Contenu du document (question + réponse)"
    )
    embedding = models.JSONField(
        help_text="Vecteur d'embedding 384D généré par all-MiniLM-L6-v2"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Métadonnées du document (question, answer, source, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rag_documentembedding'
        verbose_name = 'Document Embedding'
        verbose_name_plural = 'Document Embeddings'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['metadata']),
            # Index GIN pour les recherches JSONB efficaces
            GinIndex(fields=['metadata']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        question = self.metadata.get('question', 'Sans question')[:50]
        return f"Document {self.id}: {question}..."
    
    @property
    def content(self):
        """Propriété pour compatibilité avec l'ancien code"""
        return self.content_text
    
    def get_question(self):
        """Retourne la question du document"""
        return self.metadata.get('question', '')
    
    def get_answer(self):
        """Retourne la réponse du document"""
        return self.metadata.get('answer', '')
    
    def get_source(self):
        """Retourne la source du document"""
        return self.metadata.get('source', 'unknown')
    
    def is_valid_embedding(self):
        """Vérifie si l'embedding est valide (384 dimensions)"""
        if not isinstance(self.embedding, list):
            return False
        return len(self.embedding) == 384 and all(isinstance(x, (int, float)) for x in self.embedding)
    
    def get_embedding_dimension(self):
        """Retourne la dimension de l'embedding"""
        if isinstance(self.embedding, list):
            return len(self.embedding)
        return 0
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'content': self.content_text,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'metadata': self.metadata,
            'embedding_dimension': self.get_embedding_dimension(),
            'is_valid': self.is_valid_embedding(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RAGSearchLog(models.Model):
    """
    Modèle pour logger les recherches RAG pour le monitoring.
    """
    query = models.TextField(help_text="Requête de recherche")
    method = models.CharField(
        max_length=20,
        choices=[
            ('vectorial', 'Recherche Vectorielle'),
            ('heuristic', 'Recherche Heuristique'),
            ('hybrid', 'Mode Hybride')
        ],
        help_text="Méthode de recherche utilisée"
    )
    results_count = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de résultats trouvés"
    )
    response_time_ms = models.FloatField(
        help_text="Temps de réponse en millisecondes"
    )
    similarity_threshold = models.FloatField(
        default=0.7,
        help_text="Seuil de similarité utilisé"
    )
    success = models.BooleanField(
        default=True,
        help_text="Recherche réussie ou non"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Message d'erreur si échec"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rag_search_log'
        verbose_name = 'RAG Search Log'
        verbose_name_plural = 'RAG Search Logs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['method']),
            models.Index(fields=['success']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search {self.id}: {self.query[:30]}... ({self.method})"
    
    @classmethod
    def log_search(cls, query, method, results_count, response_time_ms, 
                   similarity_threshold=0.7, success=True, error_message=None):
        """Méthode utilitaire pour logger une recherche"""
        return cls.objects.create(
            query=query,
            method=method,
            results_count=results_count,
            response_time_ms=response_time_ms,
            similarity_threshold=similarity_threshold,
            success=success,
            error_message=error_message
        )