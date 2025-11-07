"""
Management command pour nettoyer les comptes système de l'annuaire
Usage: python manage.py cleanup_system_accounts
"""
from django.core.management.base import BaseCommand
from annuaire.models import Employee


class Command(BaseCommand):
    help = 'Désactive les comptes système qui ne doivent pas être dans l\'annuaire'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Supprime définitivement les comptes au lieu de les désactiver',
        )

    def handle(self, *args, **options):
        delete = options['delete']
        
        # Liste des comptes système à exclure
        system_accounts = [
            'docubase',
            'sc1adm',
            'SAPServiceSC1',
            'ISEADMIN',
            'user.test.01',
            'solarwinds',
            'SAC_FTP',
            'SQLSERVICE',
            'Administrateur',
            'ASPNET',
        ]
        
        # Rechercher les comptes système par email (format attendu: system_account@sar.sn)
        system_emails = [f"{acc}@sar.sn" for acc in system_accounts]
        system_employees = Employee.objects.filter(email__in=system_emails)
        
        count = system_employees.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun compte système trouvé à nettoyer"))
            return
        
        self.stdout.write(f"🔍 {count} compte(s) système trouvé(s)")
        
        if delete:
            system_employees.delete()
            self.stdout.write(self.style.SUCCESS(f"✅ {count} compte(s) système supprimé(s) définitivement"))
        else:
            system_employees.update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f"✅ {count} compte(s) système désactivé(s)"))
        
        # Afficher la liste des comptes traités
        for emp in system_employees:
            action = "supprimé" if delete else "désactivé"
            self.stdout.write(f"  - {emp.email} ({emp.full_name}) → {action}")

