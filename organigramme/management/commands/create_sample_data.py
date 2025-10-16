from django.core.management.base import BaseCommand
from organigramme.models import Direction, Agent


class Command(BaseCommand):
    help = 'Crée des données d\'exemple pour l\'organigramme'

    def handle(self, *args, **options):
        # Créer des directions
        directions_data = [
            'Direction Commerciale et Marketing',
            'Administration',
            'Direction des Ressources Humaines',
            'Direction EXECUTIVE - SUPPORT',
            'Direction Technique',
            'Direction Executif',
            'Direction Qualité',
            'Direction Financière',
            'Direction IT',
            'Direction Logistique',
            'Direction Sécurité'
        ]

        directions = []
        for name in directions_data:
            direction, created = Direction.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'Direction créée: {name}')
            directions.append(direction)

        # Créer des agents
        agents_data = [
            {
                'first_name': 'Amadou',
                'last_name': 'DIAGNE',
                'job_title': 'Directeur Général',
                'email': 'amadou.diagne@sar.sn',
                'phone_fixed': '+221 33 825 00 01',
                'phone_mobile': '77 123 45 67',
                'matricule': 'SAR001',
                'main_direction': directions[5],  # Direction Executif
                'manager': None,  # DG n'a pas de manager
                'hierarchy_level': 1
            },
            {
                'first_name': 'Fatou',
                'last_name': 'FALL',
                'job_title': 'Directrice Commerciale',
                'email': 'fatou.fall@sar.sn',
                'phone_fixed': '+221 33 825 00 02',
                'phone_mobile': '77 234 56 78',
                'matricule': 'SAR002',
                'main_direction': directions[0],  # Direction Commerciale
                'manager': None,  # Directrice, sera mise à jour après
                'hierarchy_level': 2
            },
            {
                'first_name': 'Moussa',
                'last_name': 'NDIAYE',
                'job_title': 'Directeur Technique',
                'email': 'moussa.ndiaye@sar.sn',
                'phone_fixed': '+221 33 825 00 03',
                'phone_mobile': '77 345 67 89',
                'matricule': 'SAR003',
                'main_direction': directions[4],  # Direction Technique
                'manager': None,  # Directeur, sera mise à jour après
                'hierarchy_level': 2
            },
            {
                'first_name': 'Aïcha',
                'last_name': 'SARR',
                'job_title': 'Responsable RH',
                'email': 'aicha.sarr@sar.sn',
                'phone_fixed': '+221 33 825 00 04',
                'phone_mobile': '77 456 78 90',
                'matricule': 'SAR004',
                'main_direction': directions[2],  # Direction RH
                'manager': None,  # Responsable, sera mise à jour après
                'hierarchy_level': 2
            },
            {
                'first_name': 'Ibrahima',
                'last_name': 'BA',
                'job_title': 'Développeur Senior',
                'email': 'ibrahima.ba@sar.sn',
                'phone_fixed': '+221 33 825 00 05',
                'phone_mobile': '77 567 89 01',
                'matricule': 'SAR005',
                'main_direction': directions[8],  # Direction IT
                'manager': None,  # Développeur, sera mise à jour après
                'hierarchy_level': 3
            }
        ]

        agents = []
        for agent_data in agents_data:
            agent, created = Agent.objects.get_or_create(
                matricule=agent_data['matricule'],
                defaults=agent_data
            )
            if created:
                self.stdout.write(f'Agent créé: {agent_data["first_name"]} {agent_data["last_name"]}')
            agents.append(agent)

        # Mettre à jour les managers
        if len(agents) >= 5:
            # Le DG (index 0) n'a pas de manager
            # Les directeurs (index 1, 2, 3) ont le DG comme manager
            agents[1].manager = agents[0]  # Fatou FALL -> Amadou DIAGNE
            agents[1].save()
            
            agents[2].manager = agents[0]  # Moussa NDIAYE -> Amadou DIAGNE
            agents[2].save()
            
            agents[3].manager = agents[0]  # Aïcha SARR -> Amadou DIAGNE
            agents[3].save()
            
            # Le développeur (index 4) a le directeur technique comme manager
            agents[4].manager = agents[2]  # Ibrahima BA -> Moussa NDIAYE
            agents[4].save()

        # Associer les agents aux directions
        agents[0].directions.add(directions[5])  # DG -> Direction Executif
        agents[1].directions.add(directions[0])  # Fatou -> Direction Commerciale
        agents[2].directions.add(directions[4])  # Moussa -> Direction Technique
        agents[3].directions.add(directions[2])  # Aïcha -> Direction RH
        agents[4].directions.add(directions[8])  # Ibrahima -> Direction IT

        # Reconstruire la hiérarchie
        Agent.rebuild_hierarchy_levels()

        self.stdout.write(
            self.style.SUCCESS('Données d\'exemple créées avec succès!')
        )
