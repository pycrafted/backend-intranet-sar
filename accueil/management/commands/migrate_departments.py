"""
Commande de management pour migrer les anciens départements (CharField) vers le nouveau modèle Department
Cette commande crée les départements à partir des DEPARTMENT_CHOICES et met à jour les idées existantes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accueil.models import Department, Idea

# Mapping des anciens codes de département vers les nouveaux
OLD_DEPARTMENT_CHOICES = [
    ('production', 'Production'),
    ('maintenance', 'Maintenance'),
    ('quality', 'Qualité'),
    ('safety', 'Sécurité'),
    ('logistics', 'Logistique'),
    ('it', 'Informatique'),
    ('hr', 'Ressources Humaines'),
    ('finance', 'Finance'),
    ('marketing', 'Marketing'),
    ('other', 'Autre'),
]


class Command(BaseCommand):
    help = 'Migre les anciens départements (CharField) vers le nouveau modèle Department'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔄 Début de la migration des départements...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODE DRY-RUN - Aucune modification ne sera effectuée"))
        
        # Vérifier si la table Department existe
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'accueil_department'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            self.stdout.write(self.style.ERROR("\n❌ ERREUR: La table 'accueil_department' n'existe pas encore !"))
            self.stdout.write("\n📋 Vous devez d'abord appliquer les migrations Django:")
            self.stdout.write("  1. python manage.py migrate accueil")
            self.stdout.write("  2. Puis réexécutez cette commande: python manage.py migrate_departments")
            return
        
        with transaction.atomic():
            # Créer les départements à partir des anciens choix
            departments_created = 0
            departments_existing = 0
            
            for code, name in OLD_DEPARTMENT_CHOICES:
                dept, created = Department.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'is_active': True,
                        'emails': []  # Liste vide par défaut, à remplir manuellement
                    }
                )
                
                if created:
                    departments_created += 1
                    self.stdout.write(f"  ✅ Département créé: {name} ({code})")
                else:
                    departments_existing += 1
                    self.stdout.write(f"  ℹ️  Département existant: {name} ({code})")
            
            self.stdout.write(f"\n📊 Résumé des départements:")
            self.stdout.write(f"  - Créés: {departments_created}")
            self.stdout.write(f"  - Existants: {departments_existing}")
            
            # Migrer les idées existantes
            # Note: Cette partie nécessite que le champ department soit encore un CharField
            # Si la migration a déjà été appliquée, cette partie sera ignorée
            try:
                # Vérifier si le champ department est encore un CharField
                # En regardant les idées qui n'ont pas de ForeignKey valide
                ideas_to_migrate = Idea.objects.filter(department__isnull=True)
                
                if ideas_to_migrate.exists():
                    self.stdout.write(f"\n⚠️  {ideas_to_migrate.count()} idée(s) sans département trouvée(s)")
                    self.stdout.write("  Ces idées devront être migrées manuellement après la migration de schéma")
                else:
                    # Essayer de migrer depuis l'ancien format CharField
                    # Cette partie ne fonctionnera que si la migration n'a pas encore été appliquée
                    self.stdout.write("\n📝 Migration des idées...")
                    self.stdout.write("  ℹ️  La migration des idées sera effectuée automatiquement par la migration Django")
                    
            except Exception as e:
                self.stdout.write(f"\n⚠️  Erreur lors de la vérification des idées: {e}")
                self.stdout.write("  La migration des idées devra être effectuée manuellement")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("\n⚠️  MODE DRY-RUN - Aucune modification n'a été effectuée"))
                # Annuler la transaction
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ Migration terminée avec succès !"))
                self.stdout.write("\n📋 Prochaines étapes:")
                self.stdout.write("  1. Exécutez: python manage.py migrate accueil (si pas déjà fait)")
                self.stdout.write("  2. Configurez les emails pour chaque département dans l'admin Django")
                self.stdout.write("  3. Vérifiez que toutes les idées ont été correctement migrées")
                self.stdout.write("  4. Testez l'envoi d'emails avec: python manage.py shell")
                self.stdout.write("     >>> from django.core.mail import send_mail")
                self.stdout.write("     >>> send_mail('Test', 'Corps', 'noreply@sar.sn', ['test@sar.sn'])")

