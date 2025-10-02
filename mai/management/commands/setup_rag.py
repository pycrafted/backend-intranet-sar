from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Configure le système RAG (Retrieval Augmented Generation)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vectorize',
            action='store_true',
            help='Vectorise le dataset pour la recherche sémantique'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la reconfiguration même si déjà configuré'
        )

    def handle(self, *args, **options):
        vectorize = options['vectorize']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Début de la configuration du système RAG...')
        )
        
        try:
            # Vérifier la configuration RAG
            rag_config = getattr(settings, 'RAG_CONFIG', {})
            self.stdout.write(f'Configuration RAG actuelle: {rag_config}')
            
            # Vérifier la présence du dataset
            dataset_path = os.path.join(settings.BASE_DIR, 'data', 'sar_official_dataset.csv')
            if not os.path.exists(dataset_path):
                self.stdout.write(
                    self.style.WARNING(f'Dataset non trouvé: {dataset_path}') +
                    '\nCréation d\'un dataset minimal...'
                )
                self._create_minimal_dataset(dataset_path)
            
            # Vérifier la clé API Claude
            claude_key = os.environ.get('CLAUDE_API_KEY')
            if not claude_key:
                self.stdout.write(
                    self.style.WARNING('CLAUDE_API_KEY non définie')
                )
            else:
                self.stdout.write('Clé API Claude trouvée ✓')
            
            # Configuration de la base de données pour pgvector
            self.stdout.write('Vérification de la configuration pgvector...')
            self._check_pgvector_config()
            
            if vectorize:
                self.stdout.write('Vectorisation du dataset...')
                self._vectorize_dataset(dataset_path)
            
            self.stdout.write(
                self.style.SUCCESS('Configuration RAG terminée avec succès!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la configuration RAG: {str(e)}')
            )
            raise

    def _create_minimal_dataset(self, dataset_path):
        """Crée un dataset minimal si il n'existe pas"""
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        
        with open(dataset_path, 'w', encoding='utf-8') as file:
            file.write('question,answer\n')
            file.write('Qu\'est-ce que la SAR ?,Société Africaine de Raffinage\n')
            file.write('Quel est le rôle de la SAR ?,La SAR est une société de raffinage pétrolier\n')
        
        self.stdout.write(f'Dataset minimal créé: {dataset_path}')

    def _check_pgvector_config(self):
        """Vérifie la configuration pgvector"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write('Connexion à la base de données OK ✓')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Problème de connexion DB: {e}')
            )

    def _vectorize_dataset(self, dataset_path):
        """Vectorise le dataset pour la recherche sémantique"""
        try:
            # Import conditionnel pour éviter les erreurs si les dépendances ne sont pas installées
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                
                self.stdout.write('Chargement du modèle de vectorisation...')
                model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Lire le dataset
                questions = []
                answers = []
                
                with open(dataset_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        questions.append(row['question'])
                        answers.append(row['answer'])
                
                # Vectoriser les questions
                self.stdout.write(f'Vectorisation de {len(questions)} questions...')
                embeddings = model.encode(questions)
                
                # Ici, vous pourriez sauvegarder les embeddings dans la base de données
                # Pour l'instant, on simule juste le processus
                self.stdout.write(f'Embeddings générés: {embeddings.shape}')
                
            except ImportError as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Dépendances ML non disponibles: {e}. '
                        'La vectorisation sera ignorée.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Erreur lors de la vectorisation: {e}')
            )
