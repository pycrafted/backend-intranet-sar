"""
Management command pour forcer l'activation de TOUS les utilisateurs Django
Usage: python manage.py force_activate_all_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Force l\'activation de tous les utilisateurs Django (tous les comptes doivent être actifs)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("=" * 80)
        self.stdout.write("🔗 FORCE ACTIVATION DE TOUS LES COMPTES UTILISATEURS")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé - aucune modification ne sera effectuée"))
        
        # Récupérer tous les utilisateurs inactifs
        inactive_users = User.objects.filter(is_active=False)
        count = inactive_users.count()
        
        self.stdout.write(f"\n📊 {count} utilisateur(s) inactif(s) trouvé(s)")
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Tous les comptes sont déjà actifs !"))
        else:
            if dry_run:
                self.stdout.write(f"\n🔍 [DRY-RUN] Ces utilisateurs seraient activés:")
                for user in inactive_users[:20]:
                    self.stdout.write(f"  - {user.email or user.username:40} | {user.first_name} {user.last_name}")
                if count > 20:
                    self.stdout.write(f"  ... et {count - 20} autre(s)")
            else:
                # Activer tous les utilisateurs
                activated_count = inactive_users.update(is_active=True)
                self.stdout.write(self.style.SUCCESS(f"✅ {activated_count} utilisateur(s) activé(s)"))
                
                # Afficher quelques exemples
                if inactive_users.exists():
                    self.stdout.write("\nExemples d'utilisateurs activés:")
                    for user in inactive_users[:10]:
                        self.stdout.write(f"  - {user.email or user.username:40} | {user.first_name} {user.last_name}")
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("✅ Opération terminée !")
        self.stdout.write("💡 Tous les comptes sont maintenant actifs")
        self.stdout.write("💡 Les nouveaux comptes créés seront automatiquement actifs")
        self.stdout.write("=" * 80)


