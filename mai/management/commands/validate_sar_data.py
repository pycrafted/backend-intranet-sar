"""
Commande de validation des données SAR ingérées.
Vérifie la qualité, la cohérence et les performances.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from mai.models import DocumentEmbedding, RAGSearchLog
from mai.vector_search_service import vector_search_service
from mai.embedding_service import embedding_service
import json
import time


class Command(BaseCommand):
    help = 'Valide la qualité des données SAR ingérées'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Validation détaillée avec exemples'
        )
        parser.add_argument(
            '--test-search',
            action='store_true',
            help='Tester les performances de recherche'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Tenter de corriger les problèmes détectés'
        )
    
    def handle(self, *args, **options):
        """Exécute la validation des données SAR"""
        self.stdout.write(
            self.style.SUCCESS('=== Validation des Données SAR ===')
        )
        
        try:
            # 1. Validation de base
            self.validate_basic_data()
            
            # 2. Validation des embeddings
            self.validate_embeddings()
            
            # 3. Validation des métadonnées
            self.validate_metadata()
            
            # 4. Test de recherche si demandé
            if options['test_search']:
                self.test_search_performance()
            
            # 5. Validation détaillée si demandée
            if options['detailed']:
                self.detailed_validation()
            
            # 6. Correction des problèmes si demandée
            if options['fix_issues']:
                self.fix_issues()
            
            self.stdout.write(
                self.style.SUCCESS('=== Validation terminée avec succès ! ===')
            )
            
        except Exception as e:
            raise CommandError(f'Erreur lors de la validation: {e}')
    
    def validate_basic_data(self):
        """Validation de base des données"""
        self.stdout.write('\n[VALIDATION] Validation de base...')
        
        # Compter les documents SAR
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )
        total_count = sar_docs.count()
        
        if total_count == 0:
            raise CommandError('Aucun document SAR trouvé en base')
        
        self.stdout.write(f'  [OK] Documents SAR: {total_count}')
        
        # Vérifier la répartition par type de contenu
        content_types = sar_docs.values_list('content_type', flat=True).distinct()
        self.stdout.write(f'  [OK] Types de contenu: {list(content_types)}')
        
        # Vérifier les dates de création
        from django.utils import timezone
        from datetime import timedelta
        
        recent_docs = sar_docs.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        self.stdout.write(f'  [OK] Documents récents (24h): {recent_docs}')
        
        # Vérifier la cohérence des IDs
        content_ids = sar_docs.values_list('content_id', flat=True)
        unique_ids = len(set(content_ids))
        self.stdout.write(f'  [OK] IDs uniques: {unique_ids}/{total_count}')
        
        if unique_ids != total_count:
            self.stdout.write(f'  [WARN] {total_count - unique_ids} IDs dupliqués détectés')
    
    def validate_embeddings(self):
        """Validation des embeddings"""
        self.stdout.write('\n[EMBEDDINGS] Validation des embeddings...')
        
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )
        
        # Vérifier la dimension des embeddings
        invalid_dimensions = 0
        invalid_types = 0
        nan_values = 0
        
        for doc in sar_docs[:100]:  # Échantillon de 100
            try:
                if not doc.is_valid_embedding():
                    invalid_dimensions += 1
                    continue
                
                # Vérifier les valeurs NaN
                if any(str(x).lower() in ['nan', 'inf', '-inf'] for x in doc.embedding):
                    nan_values += 1
                
            except Exception as e:
                invalid_types += 1
                continue
        
        self.stdout.write(f'  [OK] Embeddings valides: {100 - invalid_dimensions - invalid_types}/100')
        
        if invalid_dimensions > 0:
            self.stdout.write(f'  [WARN] {invalid_dimensions} embeddings avec mauvaise dimension')
        
        if invalid_types > 0:
            self.stdout.write(f'  [WARN] {invalid_types} embeddings avec type invalide')
        
        if nan_values > 0:
            self.stdout.write(f'  [WARN] {nan_values} embeddings avec valeurs NaN/Inf')
        
        # Test de génération d'embedding
        test_text = "Test de validation des embeddings"
        try:
            start_time = time.time()
            test_embedding = embedding_service.generate_embedding(test_text)
            generation_time = time.time() - start_time
            
            self.stdout.write(f'  [OK] Test génération: {generation_time*1000:.1f}ms')
            self.stdout.write(f'  [OK] Dimension test: {len(test_embedding)}')
            
        except Exception as e:
            self.stdout.write(f'  [ERROR] Erreur génération test: {e}')
    
    def validate_metadata(self):
        """Validation des métadonnées"""
        self.stdout.write('\n[METADATA] Validation des métadonnées...')
        
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )
        
        # Vérifier la structure des métadonnées
        required_fields = ['question', 'answer', 'source', 'original_id']
        missing_fields = {field: 0 for field in required_fields}
        
        empty_questions = 0
        empty_answers = 0
        invalid_json = 0
        
        for doc in sar_docs[:100]:  # Échantillon de 100
            try:
                metadata = doc.metadata
                
                # Vérifier les champs requis
                for field in required_fields:
                    if field not in metadata:
                        missing_fields[field] += 1
                
                # Vérifier les questions/réponses vides
                if not metadata.get('question', '').strip():
                    empty_questions += 1
                
                if not metadata.get('answer', '').strip():
                    empty_answers += 1
                
            except Exception as e:
                invalid_json += 1
                continue
        
        # Afficher les résultats
        for field, count in missing_fields.items():
            if count > 0:
                self.stdout.write(f'  [WARN] {count} documents sans champ "{field}"')
            else:
                self.stdout.write(f'  [OK] Champ "{field}": présent')
        
        if empty_questions > 0:
            self.stdout.write(f'  [WARN] {empty_questions} questions vides')
        
        if empty_answers > 0:
            self.stdout.write(f'  [WARN] {empty_answers} réponses vides')
        
        if invalid_json > 0:
            self.stdout.write(f'  [ERROR] {invalid_json} métadonnées JSON invalides')
    
    def test_search_performance(self):
        """Test des performances de recherche"""
        self.stdout.write('\n[PERFORMANCE] Test des performances de recherche...')
        
        # Requêtes de test
        test_queries = [
            "Quelle est la date d'inauguration de la SAR ?",
            "Quelle est la capacité de la SAR ?",
            "Quels sont les produits de la SAR ?",
            "Qui est le président de la SAR ?",
            "Où se trouve la SAR ?"
        ]
        
        total_time = 0
        total_results = 0
        successful_searches = 0
        
        for i, query in enumerate(test_queries, 1):
            try:
                start_time = time.time()
                results = vector_search_service.search_similar(
                    query, 
                    limit=3, 
                    threshold=0.1
                )
                search_time = time.time() - start_time
                
                total_time += search_time
                total_results += len(results)
                successful_searches += 1
                
                self.stdout.write(f'  [OK] Requête {i}: {search_time*1000:.1f}ms, {len(results)} résultats')
                
            except Exception as e:
                self.stdout.write(f'  [ERROR] Requête {i} échouée: {e}')
        
        if successful_searches > 0:
            avg_time = total_time / successful_searches
            avg_results = total_results / successful_searches
            
            self.stdout.write(f'\n  [STATS] Temps moyen: {avg_time*1000:.1f}ms')
            self.stdout.write(f'  [STATS] Résultats moyens: {avg_results:.1f}')
            self.stdout.write(f'  [STATS] Taux de succès: {successful_searches}/{len(test_queries)}')
            
            # Validation des performances
            if avg_time < 0.1:  # < 100ms
                self.stdout.write('  [OK] Performances de recherche excellentes')
            elif avg_time < 0.5:  # < 500ms
                self.stdout.write('  [OK] Performances de recherche bonnes')
            else:
                self.stdout.write('  [WARN] Performances de recherche à améliorer')
    
    def detailed_validation(self):
        """Validation détaillée avec exemples"""
        self.stdout.write('\n[DETAILED] Validation détaillée...')
        
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )[:5]  # 5 premiers documents
        
        self.stdout.write(f'  [INFO] Analyse de {len(sar_docs)} documents:')
        
        for i, doc in enumerate(sar_docs, 1):
            self.stdout.write(f'\n    Document {i}:')
            self.stdout.write(f'      ID: {doc.id}')
            self.stdout.write(f'      Type: {doc.content_type}')
            self.stdout.write(f'      Content ID: {doc.content_id}')
            self.stdout.write(f'      Question: {doc.get_question()[:60]}...')
            self.stdout.write(f'      Answer: {doc.get_answer()[:60]}...')
            self.stdout.write(f'      Embedding valide: {doc.is_valid_embedding()}')
            self.stdout.write(f'      Dimension: {doc.get_embedding_dimension()}')
            self.stdout.write(f'      Créé: {doc.created_at}')
            
            # Vérifier les métadonnées
            metadata = doc.metadata
            self.stdout.write(f'      Métadonnées: {len(metadata)} champs')
            for key, value in metadata.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + '...'
                self.stdout.write(f'        {key}: {value}')
    
    def fix_issues(self):
        """Tente de corriger les problèmes détectés"""
        self.stdout.write('\n[FIX] Correction des problèmes...')
        
        # Corriger les métadonnées JSON invalides
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )
        
        fixed_count = 0
        for doc in sar_docs:
            try:
                # Tenter d'accéder aux métadonnées
                metadata = doc.metadata
                
                # Vérifier et corriger les champs manquants
                if 'source' not in metadata:
                    metadata['source'] = 'sar_official_dataset.csv'
                
                if 'original_id' not in metadata:
                    metadata['original_id'] = doc.content_id
                
                # Sauvegarder si modifié
                doc.save()
                fixed_count += 1
                
            except Exception as e:
                self.stdout.write(f'  [ERROR] Impossible de corriger document {doc.id}: {e}')
                continue
        
        self.stdout.write(f'  [OK] {fixed_count} documents corrigés')
    
    def get_statistics(self):
        """Retourne les statistiques des données"""
        sar_docs = DocumentEmbedding.objects.filter(
            metadata__source='sar_official_dataset.csv'
        )
        
        return {
            'total_documents': sar_docs.count(),
            'valid_embeddings': sum(1 for doc in sar_docs[:100] if doc.is_valid_embedding()),
            'content_types': list(sar_docs.values_list('content_type', flat=True).distinct()),
            'date_range': {
                'earliest': sar_docs.earliest('created_at').created_at,
                'latest': sar_docs.latest('created_at').created_at
            }
        }
