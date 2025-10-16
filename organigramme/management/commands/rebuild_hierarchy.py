from django.core.management.base import BaseCommand
from django.db import models
from organigramme.models import Agent


class Command(BaseCommand):
    help = 'Reconstruit tous les niveaux hiérarchiques des agents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show',
            action='store_true',
            help='Afficher la hiérarchie après reconstruction',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔄 Reconstruction des niveaux hiérarchiques...')
        
        # Reconstruire la hiérarchie
        Agent.rebuild_hierarchy_levels()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Niveaux hiérarchiques reconstruits avec succès!')
        )
        
        if options['show']:
            self.show_hierarchy()

    def show_hierarchy(self):
        """Affiche la hiérarchie complète"""
        self.stdout.write('\n📊 Hiérarchie des agents:')
        self.stdout.write('=' * 50)
        
        # Afficher par niveau hiérarchique
        agents_by_level = {}
        for agent in Agent.objects.all().order_by('hierarchy_level', 'last_name'):
            level = agent.hierarchy_level
            if level not in agents_by_level:
                agents_by_level[level] = []
            agents_by_level[level].append(agent)
        
        for level in sorted(agents_by_level.keys()):
            self.stdout.write(f'\n🏢 Niveau {level}:')
            for agent in agents_by_level[level]:
                manager_info = f" → Manager: {agent.manager.full_name}" if agent.manager else " → DG"
                self.stdout.write(f"  • {agent.full_name} ({agent.job_title}){manager_info}")
        
        # Afficher les statistiques
        self.stdout.write('\n📈 Statistiques:')
        self.stdout.write(f"  • Total agents: {Agent.objects.count()}")
        self.stdout.write(f"  • DG (niveau 1): {Agent.objects.filter(hierarchy_level=1).count()}")
        self.stdout.write(f"  • Niveau max: {Agent.objects.aggregate(max_level=models.Max('hierarchy_level'))['max_level'] or 0}")
        
        # Afficher les agents sans manager (problèmes potentiels)
        agents_without_manager = Agent.objects.filter(manager__isnull=True, hierarchy_level__gt=1)
        if agents_without_manager.exists():
            self.stdout.write('\n⚠️  Agents sans manager mais niveau > 1:')
            for agent in agents_without_manager:
                self.stdout.write(f"  • {agent.full_name} (niveau {agent.hierarchy_level})")
