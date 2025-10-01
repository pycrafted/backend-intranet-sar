from django.core.management.base import BaseCommand
from annuaire.models import Employee


class Command(BaseCommand):
    help = 'Met à jour tous les niveaux hiérarchiques des employés basés sur leur manager'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Début de la mise à jour des niveaux hiérarchiques...')
        )
        
        # Trouver tous les employés sans manager (niveau 1)
        ceos = Employee.objects.filter(manager__isnull=True)
        
        if not ceos.exists():
            self.stdout.write(
                self.style.WARNING('Aucun employé sans manager trouvé (CEO)')
            )
            return
        
        updated_count = 0
        
        for ceo in ceos:
            self.stdout.write(f'CEO trouvé: {ceo.full_name} (ID: {ceo.id})')
            
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Niveau calculé: {ceo.hierarchy_level}')
            else:
                # Le niveau sera automatiquement calculé par la propriété
                # On force juste la sauvegarde pour déclencher les signaux
                ceo.save()
                updated_count += 1
                self.stdout.write(f'  Niveau mis à jour: {ceo.hierarchy_level}')
            
            # Mettre à jour récursivement tous les subordonnés
            updated_count += self._update_subordinates(ceo, dry_run, 0)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY-RUN] {updated_count} employés seraient mis à jour')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{updated_count} employés mis à jour avec succès')
            )

    def _update_subordinates(self, manager, dry_run, level):
        """Met à jour récursivement les subordonnés d'un manager"""
        updated_count = 0
        subordinates = manager.subordinates.all()
        
        for subordinate in subordinates:
            indent = "  " * (level + 1)
            calculated_level = subordinate.hierarchy_level
            
            if dry_run:
                self.stdout.write(f'{indent}[DRY-RUN] {subordinate.full_name}: niveau {calculated_level}')
            else:
                subordinate.save()
                updated_count += 1
                self.stdout.write(f'{indent}{subordinate.full_name}: niveau {calculated_level}')
            
            # Récursion pour les sous-niveaux
            updated_count += self._update_subordinates(subordinate, dry_run, level + 1)
        
        return updated_count
