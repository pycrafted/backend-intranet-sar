from django.core.management.base import BaseCommand
from documents.models import DocumentCategory, DocumentFolder
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Créer des données d\'exemple pour les documents'

    def handle(self, *args, **options):
        # Créer des catégories de documents
        categories_data = [
            {
                'name': 'Ressources Humaines',
                'description': 'Documents liés aux ressources humaines',
                'color': '#3B82F6',
                'icon': 'users',
                'order': 1
            },
            {
                'name': 'Finances',
                'description': 'Documents financiers et comptables',
                'color': '#10B981',
                'icon': 'dollar-sign',
                'order': 2
            },
            {
                'name': 'Sécurité',
                'description': 'Documents de sécurité et procédures',
                'color': '#EF4444',
                'icon': 'shield',
                'order': 3
            },
            {
                'name': 'Production',
                'description': 'Documents de production et opérations',
                'color': '#F59E0B',
                'icon': 'cog',
                'order': 4
            },
            {
                'name': 'Qualité',
                'description': 'Documents de qualité et certification',
                'color': '#8B5CF6',
                'icon': 'award',
                'order': 5
            },
            {
                'name': 'Maintenance',
                'description': 'Documents de maintenance et réparation',
                'color': '#06B6D4',
                'icon': 'wrench',
                'order': 6
            },
            {
                'name': 'Formation',
                'description': 'Documents de formation et développement',
                'color': '#84CC16',
                'icon': 'book-open',
                'order': 7
            },
            {
                'name': 'Général',
                'description': 'Documents généraux et divers',
                'color': '#6B7280',
                'icon': 'file',
                'order': 8
            }
        ]

        created_categories = []
        for cat_data in categories_data:
            category, created = DocumentCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                created_categories.append(category)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Catégorie créée: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Catégorie existe déjà: {category.name}')
                )

        # Créer des dossiers racines
        folders_data = [
            {
                'name': 'Documents Officiels',
                'description': 'Documents officiels de l\'entreprise',
                'color': '#3B82F6',
                'icon': 'folder'
            },
            {
                'name': 'Procédures',
                'description': 'Procédures et manuels',
                'color': '#10B981',
                'icon': 'book'
            },
            {
                'name': 'Rapports',
                'description': 'Rapports et analyses',
                'color': '#F59E0B',
                'icon': 'bar-chart'
            },
            {
                'name': 'Formations',
                'description': 'Documents de formation',
                'color': '#8B5CF6',
                'icon': 'graduation-cap'
            }
        ]

        # Obtenir un utilisateur admin ou créer un utilisateur par défaut
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@sar.sn',
                password='admin123',
                first_name='Admin',
                last_name='SAR'
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Utilisateur admin créé')
            )

        created_folders = []
        for folder_data in folders_data:
            folder, created = DocumentFolder.objects.get_or_create(
                name=folder_data['name'],
                defaults={
                    **folder_data,
                    'created_by': admin_user
                }
            )
            if created:
                created_folders.append(folder)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Dossier créé: {folder.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Dossier existe déjà: {folder.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Données d\'exemple créées avec succès!\n'
                f'📁 Catégories: {len(created_categories)}\n'
                f'📂 Dossiers: {len(created_folders)}'
            )
        )
