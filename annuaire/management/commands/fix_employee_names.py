"""
Management command pour corriger les noms vides des employés
Usage: python manage.py fix_employee_names
"""
from django.core.management.base import BaseCommand
from django.db import models
from annuaire.models import Employee


class Command(BaseCommand):
    help = 'Corrige les employés qui ont des noms vides ou incomplets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé - aucune modification ne sera effectuée"))
        
        # Trouver les employés avec des noms vides
        employees_with_empty_names = Employee.objects.filter(
            models.Q(first_name='') | models.Q(last_name='') | models.Q(first_name__isnull=True) | models.Q(last_name__isnull=True)
        )
        
        count = employees_with_empty_names.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun employé avec des noms vides trouvé"))
            return
        
        self.stdout.write(f"🔍 {count} employé(s) avec des noms vides trouvé(s)")
        
        fixed_count = 0
        
        for employee in employees_with_empty_names:
            original_first = employee.first_name or ''
            original_last = employee.last_name or ''
            
            # Corriger le prénom si vide
            if not employee.first_name or employee.first_name.strip() == '':
                if employee.last_name and employee.last_name.strip():
                    # Utiliser le nom comme prénom si le prénom est vide
                    employee.first_name = employee.last_name
                else:
                    # Utiliser l'email comme fallback (sans le @)
                    if employee.email:
                        employee.first_name = employee.email.split('@')[0]
                    else:
                        employee.first_name = "Prénom"
            
            # Corriger le nom si vide
            if not employee.last_name or employee.last_name.strip() == '':
                if employee.first_name and employee.first_name.strip():
                    # Utiliser le prénom comme nom si le nom est vide
                    employee.last_name = employee.first_name
                else:
                    # Utiliser l'email comme fallback (sans le @)
                    if employee.email:
                        employee.last_name = employee.email.split('@')[0]
                    else:
                        employee.last_name = "Nom"
            
            if dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] {employee.email}: "
                    f"'{original_first}' '{original_last}' → '{employee.first_name}' '{employee.last_name}'"
                )
            else:
                employee.save(update_fields=['first_name', 'last_name'])
                fixed_count += 1
                self.stdout.write(
                    f"  ✅ {employee.email}: "
                    f"'{original_first}' '{original_last}' → '{employee.first_name}' '{employee.last_name}'"
                )
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"✅ {fixed_count} employé(s) corrigé(s)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ {count} employé(s) seraient corrigé(s)"))

