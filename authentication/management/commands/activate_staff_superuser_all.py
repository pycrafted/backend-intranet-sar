"""
Management command pour activer le statut Staff et Superuser pour TOUS les utilisateurs Django
Usage: python manage.py activate_staff_superuser_all
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Active is_active, is_staff et is_superuser pour tous les utilisateurs Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Active uniquement is_active (pas Staff ni Superuser)',
        )
        parser.add_argument(
            '--staff-only',
            action='store_true',
            help='Active uniquement le statut Staff (pas Superuser ni Active)',
        )
        parser.add_argument(
            '--superuser-only',
            action='store_true',
            help='Active uniquement le statut Superuser (pas Staff ni Active)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        active_only = options['active_only']
        staff_only = options['staff_only']
        superuser_only = options['superuser_only']
        
        self.stdout.write("=" * 80)
        self.stdout.write("🔐 ACTIVATION DE is_active, is_staff ET is_superuser POUR TOUS LES UTILISATEURS")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé - aucune modification ne sera effectuée"))
        
        # Déterminer quels statuts activer
        activate_active = active_only or (not staff_only and not superuser_only)
        activate_staff = staff_only or (not active_only and not superuser_only)
        activate_superuser = superuser_only or (not active_only and not staff_only)
        
        if active_only:
            self.stdout.write("\n✅ Mode: Activation uniquement de is_active")
        elif staff_only:
            self.stdout.write("\n📋 Mode: Activation uniquement du statut STAFF")
        elif superuser_only:
            self.stdout.write("\n👑 Mode: Activation uniquement du statut SUPERUSER")
        else:
            self.stdout.write("\n✅📋👑 Mode: Activation de is_active, STAFF et SUPERUSER")
        
        # Récupérer tous les utilisateurs
        all_users = User.objects.all()
        total_count = all_users.count()
        
        self.stdout.write(f"\n📊 {total_count} utilisateur(s) trouvé(s) au total")
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING("⚠️ Aucun utilisateur trouvé dans la base de données"))
            return
        
        # Compter les utilisateurs qui doivent être mis à jour
        filters = {}
        if activate_active:
            filters['is_active'] = False
        if activate_staff:
            filters['is_staff'] = False
        if activate_superuser:
            filters['is_superuser'] = False
        
        if filters:
            from django.db.models import Q
            query = Q()
            for key, value in filters.items():
                query |= Q(**{key: value})
            users_to_update = all_users.filter(query).distinct()
        else:
            users_to_update = User.objects.none()
        
        update_count = users_to_update.count()
        
        # Compter les utilisateurs déjà configurés
        config_filters = {}
        if activate_active:
            config_filters['is_active'] = True
        if activate_staff:
            config_filters['is_staff'] = True
        if activate_superuser:
            config_filters['is_superuser'] = True
        
        if config_filters:
            already_configured = all_users.filter(**config_filters).count()
        else:
            already_configured = 0
        
        self.stdout.write(f"✅ {already_configured} utilisateur(s) déjà configuré(s)")
        self.stdout.write(f"🔄 {update_count} utilisateur(s) à mettre à jour")
        
        if update_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ Tous les utilisateurs ont déjà les statuts activés !"))
        else:
            if dry_run:
                self.stdout.write(f"\n🔍 [DRY-RUN] Ces utilisateurs seraient mis à jour:")
                for user in users_to_update[:20]:
                    status_info = []
                    if activate_active and not user.is_active:
                        status_info.append("Active")
                    if activate_staff and not user.is_staff:
                        status_info.append("Staff")
                    if activate_superuser and not user.is_superuser:
                        status_info.append("Superuser")
                    self.stdout.write(f"  - {user.email or user.username:40} | {user.first_name} {user.last_name} | +{', '.join(status_info)}")
                if update_count > 20:
                    self.stdout.write(f"  ... et {update_count - 20} autre(s)")
            else:
                # Mettre à jour tous les utilisateurs
                updated_count = 0
                for user in users_to_update:
                    update_fields = []
                    updated = False
                    if activate_active and not user.is_active:
                        user.is_active = True
                        update_fields.append('is_active')
                        updated = True
                    if activate_staff and not user.is_staff:
                        user.is_staff = True
                        update_fields.append('is_staff')
                        updated = True
                    if activate_superuser and not user.is_superuser:
                        user.is_superuser = True
                        update_fields.append('is_superuser')
                        updated = True
                    if updated:
                        user.save(update_fields=update_fields)
                        updated_count += 1
                
                self.stdout.write(self.style.SUCCESS(f"\n✅ {updated_count} utilisateur(s) mis à jour avec succès"))
                
                # Afficher quelques exemples
                if updated_count > 0:
                    self.stdout.write("\n📋 Exemples d'utilisateurs mis à jour:")
                    for user in users_to_update[:10]:
                        status_info = []
                        if user.is_active:
                            status_info.append("Active")
                        if user.is_staff:
                            status_info.append("Staff")
                        if user.is_superuser:
                            status_info.append("Superuser")
                        self.stdout.write(f"  - {user.email or user.username:40} | {user.first_name} {user.last_name} | Statuts: {', '.join(status_info) if status_info else 'Aucun'}")
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("✅ Opération terminée !")
        if activate_active:
            self.stdout.write("💡 Tous les utilisateurs ont maintenant is_active=True (comptes activés)")
        if activate_staff:
            self.stdout.write("💡 Tous les utilisateurs ont maintenant le statut STAFF (accès à l'admin)")
        if activate_superuser:
            self.stdout.write("💡 Tous les utilisateurs ont maintenant le statut SUPERUSER (tous les droits)")
        self.stdout.write("=" * 80)

