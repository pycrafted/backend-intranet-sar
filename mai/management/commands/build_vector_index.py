"""
Commande Django pour construire l'index vectoriel.
Usage: python manage.py build_vector_index
"""
from django.core.management.base import BaseCommand
from django.db import connection
from mai.vector_index_service import vector_index_service
from mai.models import DocumentEmbedding
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Construit l\'index vectoriel pour les recherches optimisées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--index-type',
            type=str,
            default='ivfflat',
            choices=['ivfflat', 'hnsw'],
            help='Type d\'index à construire (ivfflat ou hnsw)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la reconstruction même si l\'index existe'
        )

    def handle(self, *args, **options):
        index_type = options['index_type']
        force = options['force']
        
        self.stdout.write(f"🔧 Construction de l'index vectoriel {index_type}...")
        
        try:
            # Vérifier si l'index existe déjà
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'rag_documentembedding' 
                    AND indexname = 'rag_documentembedding_embedding_idx'
                """)
                
                existing_index = cursor.fetchone()
                
                if existing_index and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Index {index_type} existe déjà. Utilisez --force pour le reconstruire."
                        )
                    )
                    return
            
            # Vérifier qu'il y a des documents
            doc_count = DocumentEmbedding.objects.count()
            if doc_count == 0:
                self.stdout.write(
                    self.style.ERROR("Aucun document trouvé. Exécutez d'abord l'ingestion des données.")
                )
                return
            
            self.stdout.write(f"📊 {doc_count} documents trouvés")
            
            # Construire l'index
            result = vector_index_service.build_optimized_index(index_type)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Index {index_type} construit avec succès !\n"
                        f"   Durée: {result['duration_seconds']}s\n"
                        f"   Taille: {result['index_size']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur construction index: {result.get('error', 'Inconnue')}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur: {e}")
            )
            logger.error(f"Erreur construction index: {e}")
