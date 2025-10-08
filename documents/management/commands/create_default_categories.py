from django.core.management.base import BaseCommand
from documents.models import DocumentCategory

class Command(BaseCommand):
    help = 'Crée les catégories de documents par défaut'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Général',
                'description': 'Documents généraux de l\'entreprise',
                'color': '#6B7280',
                'icon': 'file',
                'order': 0
            },
            {
                'name': 'Ressources Humaines',
                'description': 'Documents liés aux ressources humaines',
                'color': '#3B82F6',
                'icon': 'users',
                'order': 1
            },
            {
                'name': 'Finance',
                'description': 'Documents financiers et comptables',
                'color': '#10B981',
                'icon': 'dollar-sign',
                'order': 2
            },
            {
                'name': 'Production',
                'description': 'Documents de production et opérations',
                'color': '#F59E0B',
                'icon': 'factory',
                'order': 3
            },
            {
                'name': 'Sécurité',
                'description': 'Documents de sécurité et conformité',
                'color': '#EF4444',
                'icon': 'shield',
                'order': 4
            },
            {
                'name': 'Qualité',
                'description': 'Documents de qualité et contrôle',
                'color': '#8B5CF6',
                'icon': 'check-circle',
                'order': 5
            },
            {
                'name': 'Maintenance',
                'description': 'Documents de maintenance et technique',
                'color': '#06B6D4',
                'icon': 'wrench',
                'order': 6
            },
            {
                'name': 'Commercial',
                'description': 'Documents commerciaux et ventes',
                'color': '#EC4899',
                'icon': 'trending-up',
                'order': 7
            },
        ]

        created_count = 0
        for cat_data in categories:
            category, created = DocumentCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Catégorie créée: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Catégorie existe déjà: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 {created_count} nouvelles catégories créées!')
        )







