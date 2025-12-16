"""
Management command pour afficher tous les utilisateurs et leurs états (is_active, is_staff, is_superuser)
Usage: python manage.py list_all_users_status
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Affiche tous les utilisateurs et leurs états (is_active, is_staff, is_superuser)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inactive-only',
            action='store_true',
            help='Afficher uniquement les utilisateurs inactifs',
        )
        parser.add_argument(
            '--no-staff-only',
            action='store_true',
            help='Afficher uniquement les utilisateurs sans statut staff',
        )
        parser.add_argument(
            '--no-superuser-only',
            action='store_true',
            help='Afficher uniquement les utilisateurs sans statut superuser',
        )

    def handle(self, *args, **options):
        inactive_only = options['inactive_only']
        no_staff_only = options['no_staff_only']
        no_superuser_only = options['no_superuser_only']
        
        self.stdout.write("=" * 100)
        self.stdout.write("📋 LISTE DE TOUS LES UTILISATEURS ET LEURS ÉTATS")
        self.stdout.write("=" * 100)
        
        # Construire la requête selon les filtres
        users_query = User.objects.all().order_by('id')
        
        if inactive_only:
            users_query = users_query.filter(is_active=False)
        if no_staff_only:
            users_query = users_query.filter(is_staff=False)
        if no_superuser_only:
            users_query = users_query.filter(is_superuser=False)
        
        all_users = users_query
        total_count = all_users.count()
        
        # Compter les différents états
        active_count = User.objects.filter(is_active=True).count()
        inactive_count = User.objects.filter(is_active=False).count()
        staff_count = User.objects.filter(is_staff=True).count()
        no_staff_count = User.objects.filter(is_staff=False).count()
        superuser_count = User.objects.filter(is_superuser=True).count()
        no_superuser_count = User.objects.filter(is_superuser=False).count()
        
        self.stdout.write(f"\n📊 STATISTIQUES GLOBALES")
        self.stdout.write(f"   Total d'utilisateurs: {User.objects.count()}")
        self.stdout.write(f"   ✅ Actifs (is_active=True): {active_count}")
        self.stdout.write(self.style.WARNING(f"   ❌ Inactifs (is_active=False): {inactive_count}"))
        self.stdout.write(f"   👤 Staff (is_staff=True): {staff_count}")
        self.stdout.write(self.style.WARNING(f"   ❌ Non-Staff (is_staff=False): {no_staff_count}"))
        self.stdout.write(f"   👑 Superuser (is_superuser=True): {superuser_count}")
        self.stdout.write(self.style.WARNING(f"   ❌ Non-Superuser (is_superuser=False): {no_superuser_count}"))
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ Aucun utilisateur trouvé avec les critères spécifiés"))
            return
        
        self.stdout.write(f"\n📋 LISTE DES UTILISATEURS ({total_count} trouvé(s))")
        self.stdout.write("=" * 100)
        self.stdout.write(f"{'ID':<6} {'Username':<25} {'Email':<35} {'Active':<8} {'Staff':<8} {'Superuser':<10} {'Nom complet'}")
        self.stdout.write("-" * 100)
        
        for user in all_users:
            active_status = "✅ Oui" if user.is_active else self.style.ERROR("❌ Non")
            staff_status = "✅ Oui" if user.is_staff else self.style.ERROR("❌ Non")
            superuser_status = "✅ Oui" if user.is_superuser else self.style.ERROR("❌ Non")
            
            full_name = f"{user.first_name} {user.last_name}".strip() or "N/A"
            
            self.stdout.write(
                f"{str(user.id):<6} "
                f"{user.username[:24]:<25} "
                f"{(user.email or 'N/A')[:34]:<35} "
                f"{active_status:<8} "
                f"{staff_status:<8} "
                f"{superuser_status:<10} "
                f"{full_name}"
            )
        
        # Afficher un résumé des problèmes
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write("⚠️  RÉSUMÉ DES PROBLÈMES")
        self.stdout.write("=" * 100)
        
        problems = []
        if inactive_count > 0:
            problems.append(f"❌ {inactive_count} utilisateur(s) inactif(s) (is_active=False)")
        if no_staff_count > 0:
            problems.append(f"❌ {no_staff_count} utilisateur(s) sans statut staff (is_staff=False)")
        if no_superuser_count > 0:
            problems.append(f"❌ {no_superuser_count} utilisateur(s) sans statut superuser (is_superuser=False)")
        
        if problems:
            for problem in problems:
                self.stdout.write(self.style.WARNING(f"   {problem}"))
            self.stdout.write("\n💡 Pour corriger ces problèmes, exécutez:")
            self.stdout.write("   python manage.py activate_staff_superuser_all")
            self.stdout.write("   python manage.py force_activate_all_users")
        else:
            self.stdout.write(self.style.SUCCESS("✅ Tous les utilisateurs sont correctement configurés !"))
        
        self.stdout.write("=" * 100)

