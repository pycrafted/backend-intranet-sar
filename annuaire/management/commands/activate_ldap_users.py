"""
Management command pour activer tous les utilisateurs Django qui ont un email
et qui sont dans LDAP (via Employee)
Usage: python manage.py activate_ldap_users
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

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔗 Début de l'activation des comptes LDAP...")
        
        # Récupérer tous les employés actifs avec email
        employees_with_email = Employee.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(
            email=''
        )
        
        self.stdout.write(f"📊 {employees_with_email.count()} employé(s) actif(s) avec email trouvé(s)")
        
        # Récupérer les emails
        ldap_emails = set()
        for emp in employees_with_email:
            email_str = emp.email.strip()
            if email_str:
                ldap_emails.add(email_str.lower())
        
        self.stdout.write(f"📧 {len(ldap_emails)} email(s) unique(s) trouvé(s)")
        
        # Activer tous les utilisateurs Django qui ont ces emails
        # Chercher par email (case-insensitive)
        users_to_activate_list = []
        for email in ldap_emails:
            try:
                user = User.objects.get(email__iexact=email, is_active=False)
                if not user.is_superuser:
                    users_to_activate_list.append(user)
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # Si plusieurs utilisateurs avec le même email, activer tous ceux qui ne sont pas superuser
                users = User.objects.filter(email__iexact=email, is_active=False).exclude(is_superuser=True)
                users_to_activate_list.extend(list(users))
        
        count = len(users_to_activate_list)
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Tous les comptes LDAP avec email sont déjà actifs !"))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f"[DRY-RUN] {count} utilisateur(s) seraient activé(s):"))
                for user in users_to_activate_list[:20]:  # Afficher les 20 premiers
                    self.stdout.write(f"  - {user.email} ({user.first_name} {user.last_name}) - ID: {user.id}")
                if count > 20:
                    self.stdout.write(f"  ... et {count - 20} autre(s)")
            else:
                # Activer tous les utilisateurs
                user_ids = [u.id for u in users_to_activate_list]
                activated_count = User.objects.filter(id__in=user_ids).update(is_active=True)
                self.stdout.write(self.style.SUCCESS(f"✅ {activated_count} utilisateur(s) activé(s)"))
                
                # Afficher quelques exemples
                if users_to_activate_list:
                    self.stdout.write("\nExemples d'utilisateurs activés:")
                    for user in users_to_activate_list[:10]:
                        self.stdout.write(f"  - {user.email} ({user.first_name} {user.last_name}) - ID: {user.id}")
        
        # Vérifier aussi les utilisateurs qui ont un email mais qui ne sont pas dans LDAP
        # (ceux-là ne doivent PAS être activés automatiquement)
        users_with_email_not_in_ldap = User.objects.filter(
            email__isnull=False
        ).exclude(
            email=''
        ).exclude(
            email__in=ldap_emails
        ).exclude(
            is_superuser=True
        )
        
        inactive_not_in_ldap = users_with_email_not_in_ldap.filter(is_active=False).count()
        active_not_in_ldap = users_with_email_not_in_ldap.filter(is_active=True).count()
        
        if inactive_not_in_ldap > 0 or active_not_in_ldap > 0:
            self.stdout.write(f"\n📋 Note: {inactive_not_in_ldap} utilisateur(s) inactif(s) et {active_not_in_ldap} utilisateur(s) actif(s) avec email mais pas dans LDAP")
            self.stdout.write("   (Ces comptes ne sont pas activés automatiquement)")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Activation terminée !"))

