"""
Commande d'ingestion intelligente du dataset SAR.
Migre les 403 Q/R vers le système vectoriel avec optimisations.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from mai.embedding_service import embedding_service
from mai.models import DocumentEmbedding, RAGSearchLog
import pandas as pd
import json
import time
import os
import csv
from pathlib import Path


class Command(BaseCommand):
    help = 'Ingère le dataset SAR dans le système vectoriel'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Taille des batches pour la génération d\'embeddings (défaut: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans insertion en base'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer l\'ingestion même si des données existent'
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Valider uniquement le dataset sans ingestion'
        )
        parser.add_argument(
            '--start-index',
            type=int,
            default=0,
            help='Index de départ pour l\'ingestion (utile pour reprendre)'
        )
        parser.add_argument(
            '--end-index',
            type=int,
            default=None,
            help='Index de fin pour l\'ingestion'
        )
    
    def handle(self, *args, **options):
        """Exécute l'ingestion du dataset SAR"""
        self.stdout.write(
            self.style.SUCCESS('=== Ingestion Intelligente du Dataset SAR ===')
        )
        
        try:
            # Configuration
            batch_size = options['batch_size']
            dry_run = options['dry_run']
            force = options['force']
            validate_only = options['validate_only']
            start_index = options['start_index']
            end_index = options['end_index']
            
            # 1. Validation du dataset
            self.validate_dataset()
            
            if validate_only:
                self.stdout.write(self.style.SUCCESS('Validation terminée avec succès !'))
                return
            
            # 2. Vérification des données existantes
            if not force and not self.check_existing_data():
                return
            
            # 3. Chargement et préparation des données
            df = self.load_and_prepare_dataset()
            
            # 4. Filtrage des données si spécifié
            if start_index > 0 or end_index is not None:
                df = self.filter_dataset(df, start_index, end_index)
            
            # 5. Ingestion par batches
            self.ingest_dataset(df, batch_size, dry_run)
            
            # 6. Validation post-ingestion
            if not dry_run:
                self.validate_ingestion()
            
            self.stdout.write(
                self.style.SUCCESS('=== Ingestion terminée avec succès ! ===')
            )
            
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'ingestion: {e}')
    
    def validate_dataset(self):
        """Valide la structure et la qualité du dataset"""
        self.stdout.write('\n[VALIDATION] Validation du dataset...')
        
        # Vérifier l'existence du fichier
        dataset_path = Path('data/sar_official_dataset.csv')
        if not dataset_path.exists():
            raise CommandError(f'Dataset non trouvé: {dataset_path}')
        
        # Charger et valider le dataset
        try:
            # Utiliser le module csv de Python pour un parsing plus robuste
            data = []
            with open(dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            
            df = pd.DataFrame(data)
            self.stdout.write(f'  [OK] Dataset chargé: {len(df)} lignes')
            
            # Vérifier les colonnes requises
            required_columns = ['question', 'answer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise CommandError(f'Colonnes manquantes: {missing_columns}')
            
            # Vérifier les données vides
            empty_questions = df['question'].isna().sum()
            empty_answers = df['answer'].isna().sum()
            
            if empty_questions > 0:
                self.stdout.write(f'  [WARN] {empty_questions} questions vides détectées')
            if empty_answers > 0:
                self.stdout.write(f'  [WARN] {empty_answers} réponses vides détectées')
            
            # Statistiques du dataset
            self.stdout.write(f'  [OK] Questions uniques: {df["question"].nunique()}')
            self.stdout.write(f'  [OK] Longueur moyenne question: {df["question"].str.len().mean():.1f} caractères')
            self.stdout.write(f'  [OK] Longueur moyenne réponse: {df["answer"].str.len().mean():.1f} caractères')
            
            # Exemples de données
            self.stdout.write('\n  [INFO] Exemples de données:')
            for i, (_, row) in enumerate(df.head(3).iterrows()):
                self.stdout.write(f'    {i+1}. Q: {row["question"][:50]}...')
                self.stdout.write(f'       A: {row["answer"][:50]}...')
            
        except Exception as e:
            raise CommandError(f'Erreur lors de la validation du dataset: {e}')
    
    def check_existing_data(self):
        """Vérifie les données existantes"""
        existing_count = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        ).count()
        
        if existing_count > 0:
            self.stdout.write(f'\n[WARN] {existing_count} documents SAR existants trouvés')
            if not self.confirm_action('Continuer l\'ingestion ?'):
                return False
            
            # Nettoyer les données existantes
            self.stdout.write('  [INFO] Nettoyage des données existantes...')
            DocumentEmbedding.objects.filter(
                metadata__source='sar_official_dataset.csv'
            ).delete()
            self.stdout.write('  [OK] Données existantes supprimées')
        
        return True
    
    def load_and_prepare_dataset(self):
        """Charge et prépare le dataset pour l'ingestion"""
        self.stdout.write('\n[PREPARATION] Chargement du dataset...')
        
        # Utiliser le module csv de Python pour un parsing plus robuste
        data = []
        with open('data/sar_official_dataset.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        df = pd.DataFrame(data)
        
        # Nettoyage des données
        df = df.dropna(subset=['question', 'answer'])
        df['question'] = df['question'].str.strip()
        df['answer'] = df['answer'].str.strip()
        
        # Filtrer les questions/réponses vides
        df = df[(df['question'] != '') & (df['answer'] != '')]
        
        # Ajouter un ID unique
        df = df.reset_index(drop=True)
        df['id'] = df.index + 1
        
        self.stdout.write(f'  [OK] Dataset préparé: {len(df)} Q/R valides')
        
        return df
    
    def filter_dataset(self, df, start_index, end_index):
        """Filtre le dataset selon les indices spécifiés"""
        if start_index > 0:
            df = df.iloc[start_index:]
            self.stdout.write(f'  [INFO] Début à l\'index {start_index}')
        
        if end_index is not None:
            df = df.iloc[:end_index]
            self.stdout.write(f'  [INFO] Fin à l\'index {end_index}')
        
        self.stdout.write(f'  [OK] Dataset filtré: {len(df)} Q/R à ingérer')
        return df
    
    def ingest_dataset(self, df, batch_size, dry_run):
        """Ingère le dataset par batches"""
        self.stdout.write(f'\n[INGESTION] Ingestion de {len(df)} Q/R...')
        
        if dry_run:
            self.stdout.write('  [DRY-RUN] Mode simulation activé')
        
        total_batches = (len(df) + batch_size - 1) // batch_size
        total_ingested = 0
        total_errors = 0
        
        start_time = time.time()
        
        for batch_idx in range(0, len(df), batch_size):
            batch_df = df.iloc[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            self.stdout.write(f'\n  [BATCH {batch_num}/{total_batches}] Traitement de {len(batch_df)} Q/R...')
            
            try:
                # Générer les embeddings par batch
                batch_start = time.time()
                texts = [f"Q: {row['question']}\nA: {row['answer']}" for _, row in batch_df.iterrows()]
                embeddings = embedding_service.generate_embeddings_batch(texts)
                embedding_time = time.time() - batch_start
                
                self.stdout.write(f'    [OK] Embeddings générés en {embedding_time:.2f}s')
                
                if not dry_run:
                    # Insérer en base par batch
                    insert_start = time.time()
                    inserted_count = self.insert_batch(batch_df, embeddings)
                    insert_time = time.time() - insert_start
                    
                    total_ingested += inserted_count
                    self.stdout.write(f'    [OK] {inserted_count} documents insérés en {insert_time:.2f}s')
                else:
                    total_ingested += len(batch_df)
                    self.stdout.write(f'    [DRY-RUN] {len(batch_df)} documents simulés')
                
            except Exception as e:
                total_errors += len(batch_df)
                self.stdout.write(f'    [ERROR] Erreur batch {batch_num}: {e}')
                continue
        
        total_time = time.time() - start_time
        
        # Statistiques finales
        self.stdout.write(f'\n[STATISTIQUES] Ingestion terminée:')
        self.stdout.write(f'  - Documents traités: {total_ingested}')
        self.stdout.write(f'  - Erreurs: {total_errors}')
        self.stdout.write(f'  - Temps total: {total_time:.2f}s')
        self.stdout.write(f'  - Temps moyen par document: {total_time/total_ingested*1000:.1f}ms')
        
        if total_errors > 0:
            self.stdout.write(self.style.WARNING(f'  - {total_errors} erreurs détectées'))
    
    def insert_batch(self, batch_df, embeddings):
        """Insère un batch de documents en base"""
        inserted_count = 0
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                for i, (_, row) in enumerate(batch_df.iterrows()):
                    try:
                        # Convertir l'embedding en format vector PostgreSQL
                        vector_str = '[' + ','.join(map(str, embeddings[i])) + ']'
                        
                        # Insérer le document
                        cursor.execute("""
                            INSERT INTO rag_documentembedding 
                            (content_type, content_id, content_text, embedding, metadata, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        """, [
                            'qa_pair',
                            row['id'],
                            f"Q: {row['question']}\nA: {row['answer']}",
                            vector_str,
                            json.dumps({
                                'question': row['question'],
                                'answer': row['answer'],
                                'source': 'sar_official_dataset.csv',
                                'original_id': row['id']
                            })
                        ])
                        
                        inserted_count += 1
                        
                    except Exception as e:
                        self.stdout.write(f'      [ERROR] Erreur insertion document {row["id"]}: {e}')
                        continue
        
        return inserted_count
    
    def validate_ingestion(self):
        """Valide l'ingestion post-traitement"""
        self.stdout.write('\n[VALIDATION] Validation post-ingestion...')
        
        # Compter les documents ingérés
        total_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        ).count()
        
        self.stdout.write(f'  [OK] Documents SAR en base: {total_docs}')
        
        # Vérifier la qualité des embeddings
        invalid_embeddings = 0
        for doc in DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )[:10]:  # Échantillon de 10
            if not doc.is_valid_embedding():
                invalid_embeddings += 1
        
        if invalid_embeddings > 0:
            self.stdout.write(f'  [WARN] {invalid_embeddings} embeddings invalides détectés')
        else:
            self.stdout.write('  [OK] Tous les embeddings sont valides')
        
        # Test de recherche
        self.stdout.write('  [INFO] Test de recherche...')
        try:
            results = DocumentEmbedding.objects.filter(
                metadata__source='sar_official_dataset.csv'
            )[:3]
            
            if results:
                self.stdout.write(f'  [OK] {len(results)} documents trouvés pour test')
                for doc in results:
                    question = doc.get_question()[:50]
                    self.stdout.write(f'    - {question}...')
            else:
                self.stdout.write('  [WARN] Aucun document trouvé pour test')
                
        except Exception as e:
            self.stdout.write(f'  [ERROR] Erreur test recherche: {e}')
    
    def confirm_action(self, message):
        """Demande confirmation à l'utilisateur"""
        try:
            response = input(f'{message} (y/N): ')
            return response.lower() in ['y', 'yes', 'oui', 'o']
        except (EOFError, KeyboardInterrupt):
            return False
