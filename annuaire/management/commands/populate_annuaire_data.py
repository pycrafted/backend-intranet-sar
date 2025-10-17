from django.core.management.base import BaseCommand
from django.db import transaction
from annuaire.models import Department, Employee
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de test pour l\'annuaire'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime toutes les données existantes avant d\'ajouter les nouvelles données',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des données existantes...')
            Employee.objects.all().delete()
            Department.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Données existantes supprimées.'))

        # Créer les départements
        departments_data = [
            "Direction Commerciale et Marketing",
            "Administration",
            "Direction des Ressources Humaines", 
            "Direction EXECUTIVE - SUPPORT",
            "Direction Technique",
            "Direction Executif",
            "Direction Financière",
            "Direction Qualité",
            "Direction Logistique",
            "Direction Communication"
        ]

        departments = {}
        for dept_name in departments_data:
            dept, created = Department.objects.get_or_create(name=dept_name)
            departments[dept_name] = dept
            if created:
                self.stdout.write(f'Département créé: {dept_name}')

        # Données des employés
        employees_data = [
            {
                "first_name": "Maimouna",
                "last_name": "DIOP DIAGNE",
                "email": "maimoumadiagne@sar.sn",
                "phone_fixed": "+221 33 825 96 21",
                "phone_mobile": "77 459 63 21",
                "employee_id": "SAR001",
                "position_title": "Directrice Commerciale et Marketing",
                "department": "Direction Commerciale et Marketing"
            },
            {
                "first_name": "Mamadou Abib",
                "last_name": "DIOP",
                "email": "mamadoudiop@sar.sn",
                "phone_fixed": "+221 33 825 03 20",
                "phone_mobile": "77 250 31 20",
                "employee_id": "SAR002",
                "position_title": "Directeur général",
                "department": "Administration"
            },
            {
                "first_name": "Oumar",
                "last_name": "DIOUF",
                "email": "oumardiouf@sar.sn",
                "phone_fixed": "+221 33 825 98 31",
                "phone_mobile": None,
                "employee_id": "SAR003",
                "position_title": "Directeur des Ressources Humaines",
                "department": "Direction des Ressources Humaines"
            },
            {
                "first_name": "Souleymane",
                "last_name": "SECK",
                "email": "souleymaneseck@sar.sn",
                "phone_fixed": "+221 33 825 59 13",
                "phone_mobile": "77 145 93 13",
                "employee_id": "SAR004",
                "position_title": "Directeur EXECUTIVE - SUPPORT",
                "department": "Direction EXECUTIVE - SUPPORT"
            },
            {
                "first_name": "Ousmane",
                "last_name": "SEMBENE",
                "email": "ousmanesembene@sar.sn",
                "phone_fixed": None,
                "phone_mobile": "77 514 96 38",
                "employee_id": "SAR005",
                "position_title": "Directeur Technique",
                "department": "Direction Technique"
            },
            {
                "first_name": "Daouda",
                "last_name": "KEBE",
                "email": "daoudakebe@sar.sn",
                "phone_fixed": "+221 33 825 63 20",
                "phone_mobile": "77 256 39 20",
                "employee_id": "SAR006",
                "position_title": "Directeur EXECUTIVE OPERATIONS",
                "department": "Direction Executif"
            },
            {
                "first_name": "Fatou",
                "last_name": "DIAGNE",
                "email": "fatoudiagne@sar.sn",
                "phone_fixed": None,
                "phone_mobile": None,
                "employee_id": "SAR007",
                "position_title": "Responsable Qualité",
                "department": "Direction Qualité"
            },
            {
                "first_name": "Ibrahima",
                "last_name": "FALL",
                "email": "ibrahimafall@sar.sn",
                "phone_fixed": "+221 33 825 67 90",
                "phone_mobile": "77 456 78 90",
                "employee_id": "SAR008",
                "position_title": "Chef de Projet",
                "department": "Direction Technique"
            },
            {
                "first_name": "Aminata",
                "last_name": "SARR",
                "email": "aminatasarr@sar.sn",
                "phone_fixed": "+221 33 825 78 01",
                "phone_mobile": "77 567 89 01",
                "employee_id": "SAR009",
                "position_title": "Analyste Financier",
                "department": "Direction Financière"
            },
            {
                "first_name": "Cheikh",
                "last_name": "NDIAYE",
                "email": "cheikhndiaye@sar.sn",
                "phone_fixed": "+221 33 825 45 12",
                "phone_mobile": "77 123 45 67",
                "employee_id": "SAR010",
                "position_title": "Chef de Projet IT",
                "department": "Direction Technique"
            },
            {
                "first_name": "Khadija",
                "last_name": "DIAGNE",
                "email": "khadijadiagne@sar.sn",
                "phone_fixed": "+221 33 825 67 89",
                "phone_mobile": "77 234 56 78",
                "employee_id": "SAR011",
                "position_title": "Responsable Communication",
                "department": "Direction Commerciale et Marketing"
            },
            {
                "first_name": "Moussa",
                "last_name": "FALL",
                "email": "moussafall@sar.sn",
                "phone_fixed": "+221 33 825 34 56",
                "phone_mobile": "77 345 67 89",
                "employee_id": "SAR012",
                "position_title": "Ingénieur Système",
                "department": "Direction Technique"
            },
            {
                "first_name": "Aïcha",
                "last_name": "BA",
                "email": "aichaba@sar.sn",
                "phone_fixed": "+221 33 825 89 01",
                "phone_mobile": "77 456 78 90",
                "employee_id": "SAR013",
                "position_title": "Comptable Senior",
                "department": "Direction Financière"
            },
            {
                "first_name": "Pape",
                "last_name": "SARR",
                "email": "papesarr@sar.sn",
                "phone_fixed": "+221 33 825 12 34",
                "phone_mobile": "77 567 89 01",
                "employee_id": "SAR014",
                "position_title": "Responsable Logistique",
                "department": "Direction Logistique"
            },
            {
                "first_name": "Mariama",
                "last_name": "DIAGNE",
                "email": "mariamadiagne@sar.sn",
                "phone_fixed": "+221 33 825 56 78",
                "phone_mobile": "77 678 90 12",
                "employee_id": "SAR015",
                "position_title": "Développeuse Frontend",
                "department": "Direction Technique"
            },
            {
                "first_name": "Modou",
                "last_name": "NDIAYE",
                "email": "modoundiaye@sar.sn",
                "phone_fixed": "+221 33 825 90 12",
                "phone_mobile": "77 789 01 23",
                "employee_id": "SAR016",
                "position_title": "Chef de Service RH",
                "department": "Direction des Ressources Humaines"
            },
            {
                "first_name": "Fatou",
                "last_name": "SECK",
                "email": "fatouseck@sar.sn",
                "phone_fixed": "+221 33 825 23 45",
                "phone_mobile": "77 890 12 34",
                "employee_id": "SAR017",
                "position_title": "Analyste Business",
                "department": "Direction Commerciale et Marketing"
            },
            {
                "first_name": "Samba",
                "last_name": "FALL",
                "email": "sambafall@sar.sn",
                "phone_fixed": "+221 33 825 67 89",
                "phone_mobile": "77 901 23 45",
                "employee_id": "SAR018",
                "position_title": "Ingénieur Réseau",
                "department": "Direction Technique"
            },
            {
                "first_name": "Awa",
                "last_name": "DIAGNE",
                "email": "awadiagne@sar.sn",
                "phone_fixed": "+221 33 825 45 67",
                "phone_mobile": "77 012 34 56",
                "employee_id": "SAR019",
                "position_title": "Responsable Formation",
                "department": "Direction des Ressources Humaines"
            },
            {
                "first_name": "Mamadou",
                "last_name": "SARR",
                "email": "mamadousarr@sar.sn",
                "phone_fixed": "+221 33 825 78 90",
                "phone_mobile": "77 123 45 67",
                "employee_id": "SAR020",
                "position_title": "Chef de Projet Infrastructure",
                "department": "Direction EXECUTIVE - SUPPORT"
            },
            {
                "first_name": "Ndeye",
                "last_name": "FALL",
                "email": "ndeyefall@sar.sn",
                "phone_fixed": "+221 33 825 12 34",
                "phone_mobile": "77 234 56 78",
                "employee_id": "SAR021",
                "position_title": "Assistante de Direction",
                "department": "Administration"
            },
            {
                "first_name": "Moussa",
                "last_name": "NDIAYE",
                "email": "moussandiaye@sar.sn",
                "phone_fixed": "+221 33 825 56 78",
                "phone_mobile": "77 345 67 89",
                "employee_id": "SAR022",
                "position_title": "Développeur Backend",
                "department": "Direction Technique"
            },
            {
                "first_name": "Aminata",
                "last_name": "DIAGNE",
                "email": "aminatadiagne@sar.sn",
                "phone_fixed": "+221 33 825 78 90",
                "phone_mobile": "77 456 78 90",
                "employee_id": "SAR023",
                "position_title": "Responsable Marketing Digital",
                "department": "Direction Commerciale et Marketing"
            },
            {
                "first_name": "Cheikh",
                "last_name": "SARR",
                "email": "cheikhsarr@sar.sn",
                "phone_fixed": "+221 33 825 90 12",
                "phone_mobile": "77 567 89 01",
                "employee_id": "SAR024",
                "position_title": "Contrôleur de Gestion",
                "department": "Direction Financière"
            },
            {
                "first_name": "Fatou",
                "last_name": "NDIAYE",
                "email": "fatoundiaye@sar.sn",
                "phone_fixed": "+221 33 825 12 34",
                "phone_mobile": "77 678 90 12",
                "employee_id": "SAR025",
                "position_title": "Responsable Achats",
                "department": "Direction Logistique"
            }
        ]

        # Créer les employés
        with transaction.atomic():
            created_count = 0
            for emp_data in employees_data:
                # Récupérer le département
                dept = departments.get(emp_data['department'])
                if not dept:
                    self.stdout.write(
                        self.style.WARNING(f'Département non trouvé: {emp_data["department"]}')
                    )
                    continue

                # Créer l'employé
                employee, created = Employee.objects.get_or_create(
                    employee_id=emp_data['employee_id'],
                    defaults={
                        'first_name': emp_data['first_name'],
                        'last_name': emp_data['last_name'],
                        'email': emp_data['email'],
                        'phone_fixed': emp_data['phone_fixed'],
                        'phone_mobile': emp_data['phone_mobile'],
                        'position_title': emp_data['position_title'],
                        'department': dept
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Employé créé: {employee.full_name} - {employee.position_title}')
                else:
                    self.stdout.write(f'Employé existant: {employee.full_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Script terminé. {created_count} nouveaux employés créés.')
        )
        
        # Afficher les statistiques
        total_employees = Employee.objects.count()
        total_departments = Department.objects.count()
        
        self.stdout.write(f'Total employés: {total_employees}')
        self.stdout.write(f'Total départements: {total_departments}')
        
        # Statistiques par département
        self.stdout.write('\nRépartition par département:')
        for dept in Department.objects.all():
            count = dept.employees.count()
            self.stdout.write(f'  {dept.name}: {count} employé(s)')
