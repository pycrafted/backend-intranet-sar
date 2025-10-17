"""
Commande Django pour peupler l'organigramme avec des données de test
Usage: python manage.py populate_organigramme
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from organigramme.models import Direction, Agent
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Peuple l\'organigramme avec des données de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Vider la base de données avant d\'ajouter les données de test',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🗑️  Suppression des données existantes...')
            Agent.objects.all().delete()
            Direction.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Données supprimées'))

        with transaction.atomic():
            # Créer les directions
            directions_data = [
                {'name': 'Direction Générale', 'description': 'Direction générale de l\'entreprise'},
                {'name': 'Ressources Humaines', 'description': 'Gestion des ressources humaines'},
                {'name': 'Finances', 'description': 'Gestion financière'},
                {'name': 'Technologies', 'description': 'Département informatique'},
                {'name': 'Marketing', 'description': 'Marketing et communication'},
                {'name': 'Production', 'description': 'Production et opérations'},
            ]

            directions = {}
            for dir_data in directions_data:
                direction, created = Direction.objects.get_or_create(
                    name=dir_data['name'],
                    defaults={'description': dir_data['description']}
                )
                directions[dir_data['name']] = direction
                if created:
                    self.stdout.write(f'✅ Direction créée: {direction.name}')

            # Créer les agents
            agents_data = [
                {
                    'first_name': 'Jean',
                    'last_name': 'Dupont',
                    'email': 'jean.dupont@company.com',
                    'job_title': 'Directeur Général',
                    'main_direction_name': 'Direction Générale',
                    'manager': None,
                    'hierarchy_level': 1,
                },
                {
                    'first_name': 'Marie',
                    'last_name': 'Martin',
                    'email': 'marie.martin@company.com',
                    'job_title': 'Directrice des Ressources Humaines',
                    'main_direction_name': 'Ressources Humaines',
                    'manager': 'Jean Dupont',
                    'hierarchy_level': 2,
                },
                {
                    'first_name': 'Pierre',
                    'last_name': 'Durand',
                    'email': 'pierre.durand@company.com',
                    'job_title': 'Directeur Financier',
                    'main_direction_name': 'Finances',
                    'manager': 'Jean Dupont',
                    'hierarchy_level': 2,
                },
                {
                    'first_name': 'Sophie',
                    'last_name': 'Leroy',
                    'email': 'sophie.leroy@company.com',
                    'job_title': 'Directrice Technique',
                    'main_direction_name': 'Technologies',
                    'manager': 'Jean Dupont',
                    'hierarchy_level': 2,
                },
                {
                    'first_name': 'Antoine',
                    'last_name': 'Moreau',
                    'email': 'antoine.moreau@company.com',
                    'job_title': 'Directeur Marketing',
                    'main_direction_name': 'Marketing',
                    'manager': 'Jean Dupont',
                    'hierarchy_level': 2,
                },
                {
                    'first_name': 'Isabelle',
                    'last_name': 'Petit',
                    'email': 'isabelle.petit@company.com',
                    'job_title': 'Directrice de Production',
                    'main_direction_name': 'Production',
                    'manager': 'Jean Dupont',
                    'hierarchy_level': 2,
                },
                {
                    'first_name': 'Thomas',
                    'last_name': 'Bernard',
                    'email': 'thomas.bernard@company.com',
                    'job_title': 'Responsable RH',
                    'main_direction_name': 'Ressources Humaines',
                    'manager': 'Marie Martin',
                    'hierarchy_level': 3,
                },
                {
                    'first_name': 'Julie',
                    'last_name': 'Roux',
                    'email': 'julie.roux@company.com',
                    'job_title': 'Comptable',
                    'main_direction_name': 'Finances',
                    'manager': 'Pierre Durand',
                    'hierarchy_level': 3,
                },
                {
                    'first_name': 'Nicolas',
                    'last_name': 'Simon',
                    'email': 'nicolas.simon@company.com',
                    'job_title': 'Développeur Senior',
                    'main_direction_name': 'Technologies',
                    'manager': 'Sophie Leroy',
                    'hierarchy_level': 3,
                },
                {
                    'first_name': 'Camille',
                    'last_name': 'Michel',
                    'email': 'camille.michel@company.com',
                    'job_title': 'Chef de Projet Marketing',
                    'main_direction_name': 'Marketing',
                    'manager': 'Antoine Moreau',
                    'hierarchy_level': 3,
                },
            ]

            created_agents = {}
            for agent_data in agents_data:
                # Trouver le manager
                manager = None
                if agent_data['manager']:
                    manager = created_agents.get(agent_data['manager'])
                    if not manager:
                        # Chercher dans la base de données existante
                        try:
                            manager = Agent.objects.get(
                                first_name=agent_data['manager'].split()[0],
                                last_name=agent_data['manager'].split()[1]
                            )
                        except Agent.DoesNotExist:
                            pass

                # Trouver la direction
                direction = directions.get(agent_data['main_direction_name'])

                agent, created = Agent.objects.get_or_create(
                    email=agent_data['email'],
                    defaults={
                        'first_name': agent_data['first_name'],
                        'last_name': agent_data['last_name'],
                        'job_title': agent_data['job_title'],
                        'main_direction_name': agent_data['main_direction_name'],
                        'manager': manager,
                        'hierarchy_level': agent_data['hierarchy_level'],
                    }
                )

                if created:
                    # Ajouter la direction
                    if direction:
                        agent.directions.add(direction)
                    created_agents[f"{agent.first_name} {agent.last_name}"] = agent
                    self.stdout.write(f'✅ Agent créé: {agent.full_name} ({agent.job_title})')
                else:
                    self.stdout.write(f'ℹ️  Agent existant: {agent.full_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Organigramme peuplé avec succès! '
                f'{Direction.objects.count()} directions et {Agent.objects.count()} agents créés.'
            )
        )
