"""
Management command pour activer TOUS les utilisateurs Django qui ont un email
et qui sont dans LDAP (basé sur la présence d'un email @sar.sn ou dans Employee)
Usage: python manage.py activate_all_ldap_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from annuaire.models import Employee
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Active tous les utilisateurs Django qui ont un email et qui sont dans LDAP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force l\'activation même pour les superusers (non recommandé)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("=" * 80)
        self.stdout.write("🔗 ACTIVATION DE TOUS LES COMPTES LDAP")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé - aucune modification ne sera effectuée"))
        
        # Méthode 1: Utilisateurs avec email @sar.sn (tous sont considérés comme LDAP)
        self.stdout.write("\n📋 Méthode 1: Utilisateurs avec email @sar.sn")
        self.stdout.write("-" * 80)
        
        users_with_sar_email = User.objects.filter(
            email__iendswith='@sar.sn',
            is_active=False
        )
        
        if not force:
            users_with_sar_email = users_with_sar_email.exclude(is_superuser=True)
        
        count_sar = users_with_sar_email.count()
        self.stdout.write(f"  📊 {count_sar} utilisateur(s) avec email @sar.sn et inactif(s)")
        
        if count_sar > 0:
            if dry_run:
                self.stdout.write(f"\n  🔍 [DRY-RUN] Ces utilisateurs seraient activés:")
                for user in users_with_sar_email[:20]:
                    self.stdout.write(f"    - {user.email:40} | {user.first_name} {user.last_name}")
                if count_sar > 20:
                    self.stdout.write(f"    ... et {count_sar - 20} autre(s)")
            else:
                activated_count = users_with_sar_email.update(is_active=True)
                self.stdout.write(self.style.SUCCESS(f"  ✅ {activated_count} utilisateur(s) avec email @sar.sn activé(s)"))
        
        # Méthode 2: Utilisateurs correspondant à des Employee actifs
        self.stdout.write("\n📋 Méthode 2: Utilisateurs correspondant à des Employee actifs")
        self.stdout.write("-" * 80)
        
        # Récupérer tous les employés actifs avec email
        employees_with_email = Employee.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(
            email=''
        )
        
        self.stdout.write(f"  📊 {employees_with_email.count()} employé(s) actif(s) avec email dans LDAP")
        
        # Récupérer les emails
        ldap_emails = set()
        for emp in employees_with_email:
            email_str = emp.email.strip()
            if email_str:
                ldap_emails.add(email_str.lower())
        
        self.stdout.write(f"  📧 {len(ldap_emails)} email(s) unique(s) trouvé(s)")
        
        # Chercher les utilisateurs inactifs avec ces emails
        users_to_activate = User.objects.filter(
            email__in=[e for e in ldap_emails],
            is_active=False
        )
        
        if not force:
            users_to_activate = users_to_activate.exclude(is_superuser=True)
        
        count_employee = users_to_activate.count()
        self.stdout.write(f"  📊 {count_employee} utilisateur(s) inactif(s) correspondant à des Employee actifs")
        
        if count_employee > 0:
            if dry_run:
                self.stdout.write(f"\n  🔍 [DRY-RUN] Ces utilisateurs seraient activés:")
                for user in users_to_activate[:20]:
                    self.stdout.write(f"    - {user.email:40} | {user.first_name} {user.last_name}")
                if count_employee > 20:
                    self.stdout.write(f"    ... et {count_employee - 20} autre(s)")
            else:
                activated_count = users_to_activate.update(is_active=True)
                self.stdout.write(self.style.SUCCESS(f"  ✅ {activated_count} utilisateur(s) correspondant à des Employee activé(s)"))
        
        # Résumé total
        total_count = count_sar + count_employee
        self.stdout.write("\n" + "=" * 80)
        if dry_run:
            self.stdout.write(f"📊 [DRY-RUN] Total: {total_count} utilisateur(s) seraient activé(s)")
            self.stdout.write("\n💡 Pour appliquer ces changements, exécutez la commande sans --dry-run")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Total: {total_count} utilisateur(s) activé(s)"))
            self.stdout.write("\n💡 Tous les comptes LDAP avec email sont maintenant actifs")
        
        self.stdout.write("=" * 80)
        
        # Statistiques finales
        total_active_ldap = User.objects.filter(
            email__iendswith='@sar.sn',
            is_active=True
        ).count()
        
        total_inactive_ldap = User.objects.filter(
            email__iendswith='@sar.sn',
            is_active=False
        ).count()
        
        self.stdout.write(f"\n📊 Statistiques finales:")
        self.stdout.write(f"  - Comptes LDAP actifs: {total_active_ldap}")
        self.stdout.write(f"  - Comptes LDAP inactifs: {total_inactive_ldap}")
        
        if total_inactive_ldap > 0:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  {total_inactive_ldap} compte(s) LDAP reste(nt) inactif(s). "
                f"Ils peuvent être des superusers ou des comptes sans email."
            ))


