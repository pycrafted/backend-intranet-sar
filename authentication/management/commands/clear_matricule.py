"""
Script pour vider tous les matricules des utilisateurs Django
Le matricule n'existe pas dans LDAP et ne doit pas être rempli automatiquement
Usage: python manage.py clear_matricule [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Vide tous les matricules des utilisateurs Django (le matricule n\'existe pas dans LDAP)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )
        parser.add_argument(
            '--keep-manual',
            action='store_true',
            help='Garde les matricules qui ne correspondent pas au username (probablement renseignés manuellement)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_manual = options['keep_manual']
        
        self.stdout.write("=" * 80)
        self.stdout.write("🧹 NETTOYAGE DES MATRICULES")
        self.stdout.write("=" * 80)
        
        # Récupérer tous les utilisateurs avec un matricule
        users_with_matricule = User.objects.filter(matricule__isnull=False).exclude(matricule='')
        
        total_count = users_with_matricule.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Aucun utilisateur avec matricule trouvé"))
            return
        
        self.stdout.write(f"\n📊 {total_count} utilisateur(s) avec matricule trouvé(s)")
        
        if keep_manual:
            # Séparer les utilisateurs dont le matricule correspond au username (probablement rempli automatiquement)
            # et ceux dont le matricule est différent (probablement renseigné manuellement)
            auto_filled = []
            manual_filled = []
            
            for user in users_with_matricule:
                # Normaliser le matricule et le username pour comparaison
                matricule_normalized = str(user.matricule).lower().strip()
                username_normalized = str(user.username).lower().strip()
                email_normalized = str(user.email).lower().strip() if user.email else ""
                
                # Extraire la partie avant @ de l'email
                email_prefix = email_normalized.split('@')[0] if '@' in email_normalized else ""
                
                # Si le matricule correspond au username ou à la partie email, c'est probablement auto-rempli
                if (matricule_normalized == username_normalized or 
                    (email_prefix and matricule_normalized == email_prefix)):
                    auto_filled.append(user)
                else:
                    manual_filled.append(user)
            
            self.stdout.write(f"\n📋 Analyse:")
            self.stdout.write(f"  - {len(auto_filled)} utilisateur(s) avec matricule = username/email (probablement auto-rempli)")
            self.stdout.write(f"  - {len(manual_filled)} utilisateur(s) avec matricule différent (probablement renseigné manuellement)")
            
            if dry_run:
                self.stdout.write(f"\n🔍 [DRY-RUN] Utilisateurs dont le matricule serait vidé:")
                for user in auto_filled[:10]:
                    self.stdout.write(f"  - {user.email:40} | Matricule: {user.matricule:20} | Username: {user.username}")
                if len(auto_filled) > 10:
                    self.stdout.write(f"  ... et {len(auto_filled) - 10} autre(s)")
                
                if manual_filled:
                    self.stdout.write(f"\n🔍 [DRY-RUN] Utilisateurs dont le matricule serait conservé:")
                    for user in manual_filled[:10]:
                        self.stdout.write(f"  - {user.email:40} | Matricule: {user.matricule:20} | Username: {user.username}")
                    if len(manual_filled) > 10:
                        self.stdout.write(f"  ... et {len(manual_filled) - 10} autre(s)")
            else:
                with transaction.atomic():
                    cleared_count = 0
                    for user in auto_filled:
                        user.matricule = None
                        user.save(update_fields=['matricule'])
                        cleared_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"\n✅ {cleared_count} matricule(s) vidé(s)"))
                    self.stdout.write(f"📝 {len(manual_filled)} matricule(s) conservé(s) (probablement renseignés manuellement)"))
        else:
            # Vider tous les matricules
            if dry_run:
                self.stdout.write(f"\n🔍 [DRY-RUN] Tous les matricules seraient vidés:")
                for user in users_with_matricule[:20]:
                    self.stdout.write(f"  - {user.email:40} | Matricule: {user.matricule:20} | Username: {user.username}")
                if total_count > 20:
                    self.stdout.write(f"  ... et {total_count - 20} autre(s)")
                self.stdout.write(f"\n⚠️  {total_count} utilisateur(s) seraient affecté(s)")
            else:
                with transaction.atomic():
                    cleared_count = users_with_matricule.update(matricule=None)
                    self.stdout.write(self.style.SUCCESS(f"\n✅ {cleared_count} matricule(s) vidé(s)"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ Nettoyage terminé"))
        self.stdout.write("=" * 80)
        
        if not dry_run:
            self.stdout.write("\n💡 Note: Les nouveaux utilisateurs créés depuis LDAP n'auront plus de matricule rempli automatiquement")
            self.stdout.write("💡 Vous pouvez renseigner les matricules manuellement dans l'admin Django si nécessaire")


