-- Script d'initialisation pour pgvector
-- Ce script sera exécuté automatiquement lors du premier démarrage du conteneur

-- Activer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Créer la table des embeddings pour le RAG
CREATE TABLE IF NOT EXISTS rag_documentembedding (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    content_id INTEGER NOT NULL,
    content_text TEXT NOT NULL,
    embedding VECTOR(384),  -- Dimension pour all-MiniLM-L6-v2
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Créer l'index pour la recherche vectorielle (cosine similarity)
CREATE INDEX IF NOT EXISTS rag_documentembedding_embedding_idx 
ON rag_documentembedding USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Créer un index composite pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS rag_documentembedding_content_type_id_idx 
ON rag_documentembedding (content_type, content_id);

-- Créer un index sur les métadonnées pour les requêtes JSON
CREATE INDEX IF NOT EXISTS rag_documentembedding_metadata_idx 
ON rag_documentembedding USING GIN (metadata);

-- Afficher un message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Extension pgvector installée avec succès!';
    RAISE NOTICE 'Table rag_documentembedding créée avec les index optimisés!';
END $$;
