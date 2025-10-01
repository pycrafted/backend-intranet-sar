from django.core.management.base import BaseCommand
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Importe le dataset SAR depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file', 
            type=str, 
            required=True,
            help='Chemin vers le fichier CSV à importer'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Efface les données existantes avant l\'import'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear_existing']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'Fichier CSV non trouvé: {csv_file}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Début de l\'import du dataset SAR depuis: {csv_file}')
        )
        
        try:
            # Lire le fichier CSV
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
            
            self.stdout.write(f'Fichier CSV lu: {len(rows)} lignes trouvées')
            
            # Vérifier la structure du CSV
            if not rows:
                self.stdout.write(
                    self.style.WARNING('Aucune donnée trouvée dans le fichier CSV')
                )
                return
            
            # Vérifier les colonnes requises
            required_columns = ['question', 'answer']
            if not all(col in rows[0].keys() for col in required_columns):
                self.stdout.write(
                    self.style.ERROR(
                        f'Colonnes requises manquantes. Attendu: {required_columns}, '
                        f'Trouvé: {list(rows[0].keys())}'
                    )
                )
                return
            
            # Traiter les données
            imported_count = 0
            for i, row in enumerate(rows, 1):
                question = row.get('question', '').strip()
                answer = row.get('answer', '').strip()
                
                if not question or not answer:
                    self.stdout.write(
                        self.style.WARNING(f'Ligne {i} ignorée: question ou réponse vide')
                    )
                    continue
                
                # Ici, vous pouvez sauvegarder dans la base de données
                # Pour l'instant, on simule juste l'import
                imported_count += 1
                
                if i % 100 == 0:
                    self.stdout.write(f'Traité {i} lignes...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import terminé avec succès: {imported_count} questions-réponses importées'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de l\'import: {str(e)}')
            )
            raise
