"""
Management command pour synchroniser les employés depuis LDAP Active Directory
Usage: python manage.py sync_ldap_employees
"""
from ldap3 import Server, Connection, ALL, SUBTREE
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
from annuaire.models import Employee, Department
from decouple import config
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronise les employés depuis LDAP Active Directory de la SAR'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données',
        )
        parser.add_argument(
            '--no-avatars',
            action='store_true',
            help='Ne synchronise pas les photos de profil depuis LDAP',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sync_avatars = not options['no_avatars']
        
        self.stdout.write("🔗 Début de la synchronisation LDAP...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé - aucune modification ne sera effectuée"))

        # Configuration LDAP depuis les variables d'environnement ou settings
        ldap_server = getattr(settings, 'LDAP_SERVER', config('LDAP_SERVER', default='10.113.243.2'))
        ldap_port = getattr(settings, 'LDAP_PORT', config('LDAP_PORT', default=389, cast=int))
        ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', config('LDAP_BASE_DN', default='DC=sar,DC=sn'))
        ldap_bind_dn = getattr(settings, 'LDAP_BIND_DN', config('LDAP_BIND_DN', default='Administrateur@sar.sn'))
        ldap_bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', config('LDAP_BIND_PASSWORD', default=''))
        
        if not ldap_bind_password:
            self.stdout.write(
                self.style.ERROR(
                    "❌ LDAP_BIND_PASSWORD non configuré. "
                    "Veuillez définir cette variable dans votre fichier .env"
                )
            )
            return

        # Connexion LDAP avec ldap3
        try:
            server = Server(ldap_server, port=ldap_port, get_info=ALL)
            conn = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Connexion LDAP réussie avec {ldap_bind_dn}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Échec connexion LDAP: {e}")
            )
            return

        # Filtre LDAP pour les utilisateurs actifs (exclut les comptes système)
        # (!(userAccountControl:1.2.840.113556.1.4.803:=2)) = compte non désactivé
        # (!(sAMAccountName=*$)) = exclut les comptes machine (se terminent par $)
        # (!(sAMAccountName=HealthMailbox*)) = exclut les HealthMailbox Exchange
        # (!(sAMAccountName=IUSR_*)) = exclut les comptes IIS
        # (!(sAMAccountName=IWAM_*)) = exclut les comptes IIS
        # (!(sAMAccountName=MSOL_*)) = exclut les comptes Microsoft Online
        # (!(sAMAccountName=AAD_*)) = exclut les comptes Azure AD Connect
        # (!(sAMAccountName=ASPNET)) = exclut le compte ASP.NET
        # (!(sAMAccountName=Administrateur)) = exclut le compte admin
        # Comptes système et de test spécifiques à exclure
        filterstr = getattr(settings, 'LDAP_USER_FILTER', 
            "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
            "(!(sAMAccountName=*$))(!(sAMAccountName=HealthMailbox*))(!(sAMAccountName=IUSR_*))"
            "(!(sAMAccountName=IWAM_*))(!(sAMAccountName=MSOL_*))(!(sAMAccountName=AAD_*))"
            "(!(sAMAccountName=ASPNET))(!(sAMAccountName=Administrateur))"
            "(!(sAMAccountName=docubase))(!(sAMAccountName=sc1adm))(!(sAMAccountName=SAPServiceSC1))"
            "(!(sAMAccountName=ISEADMIN))(!(sAMAccountName=user.test.01))(!(sAMAccountName=solarwinds))"
            "(!(sAMAccountName=SAC_FTP))(!(sAMAccountName=SQLSERVICE)))")
        
        # Attributs à récupérer
        attrs = [
            'givenName',           # Prénom
            'sn',                  # Nom de famille
            'mail',                # Email
            'telephoneNumber',     # Téléphone fixe
            'mobile',              # Téléphone mobile
            'title',               # Titre du poste
            'department',          # Département
            'sAMAccountName',      # Nom d'utilisateur Windows
            'employeeID',          # Matricule (si disponible)
            'employeeNumber',      # Numéro employé alternatif
            'thumbnailPhoto',      # Photo de profil
            'displayName',         # Nom d'affichage
        ]

        try:
            self.stdout.write(f"🔍 Recherche des utilisateurs dans {ldap_base_dn}...")
            conn.search(
                search_base=ldap_base_dn,
                search_filter=filterstr,
                search_scope=SUBTREE,
                attributes=attrs
            )
            results = conn.entries
            self.stdout.write(self.style.SUCCESS(f"✅ {len(results)} utilisateurs trouvés dans LDAP"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Échec recherche LDAP: {e}"))
            conn.unbind()
            return

        created = 0
        updated = 0
        skipped = 0
        deactivated = 0
        errors = []
        ldap_employee_ids = set()  # Pour tracker les employés présents dans LDAP

        # Traiter chaque utilisateur dans une transaction
        with transaction.atomic():
            for entry in results:
                try:
                    # Vérifier que sAMAccountName existe
                    if not hasattr(entry, 'sAMAccountName') or not entry.sAMAccountName:
                        skipped += 1
                        continue

                    # Extraire les données (ldap3 retourne des objets Entry)
                    sam = str(entry.sAMAccountName) if entry.sAMAccountName else ''
                    
                    # Email (obligatoire pour Employee)
                    email = ''
                    if hasattr(entry, 'mail') and entry.mail:
                        email = str(entry.mail).strip()
                    
                    # Si pas d'email, utiliser le format sam@sar.sn
                    if not email:
                        email = f"{sam}@sar.sn"
                    
                    # Prénom
                    first_name = ''
                    if hasattr(entry, 'givenName') and entry.givenName:
                        first_name = str(entry.givenName).strip()
                    
                    # Si pas de prénom, essayer displayName
                    if not first_name and hasattr(entry, 'displayName') and entry.displayName:
                        display_name = str(entry.displayName).strip()
                        # Essayer de séparer displayName en prénom/nom
                        parts = display_name.split(' ', 1)
                        if len(parts) > 0:
                            first_name = parts[0]
                    
                    # Nom de famille
                    last_name = ''
                    if hasattr(entry, 'sn') and entry.sn:
                        last_name = str(entry.sn).strip()
                    
                    # Si pas de nom, essayer displayName
                    if not last_name and hasattr(entry, 'displayName') and entry.displayName:
                        display_name = str(entry.displayName).strip()
                        parts = display_name.split(' ', 1)
                        if len(parts) > 1:
                            last_name = parts[1]
                    
                    # Si toujours pas de prénom ou nom, utiliser sam
                    if not first_name and not last_name:
                        first_name = sam
                        last_name = sam  # Utiliser sam aussi pour le nom si aucun nom n'est trouvé
                    
                    # S'assurer qu'au moins first_name n'est pas vide
                    if not first_name:
                        first_name = sam
                    if not last_name:
                        last_name = first_name  # Utiliser le prénom comme nom si pas de nom
                    
                    # Titre du poste
                    position_title = ''
                    if hasattr(entry, 'title') and entry.title:
                        position_title = str(entry.title).strip()
                    if not position_title:
                        position_title = 'Poste non spécifié'
                    
                    # Département
                    department_name = ''
                    if hasattr(entry, 'department') and entry.department:
                        department_name = str(entry.department).strip()
                    if not department_name:
                        department_name = 'Non affecté'
                    
                    # Téléphones
                    phone_fixed = ''
                    if hasattr(entry, 'telephoneNumber') and entry.telephoneNumber:
                        phone_fixed = str(entry.telephoneNumber).strip()
                    
                    phone_mobile = ''
                    if hasattr(entry, 'mobile') and entry.mobile:
                        phone_mobile = str(entry.mobile).strip()
                    
                    # Matricule (employeeID, employeeNumber ou sAMAccountName par défaut)
                    employee_id = sam
                    if hasattr(entry, 'employeeID') and entry.employeeID:
                        emp_id = str(entry.employeeID).strip()
                        if emp_id:
                            employee_id = emp_id
                    elif hasattr(entry, 'employeeNumber') and entry.employeeNumber:
                        emp_id = str(entry.employeeNumber).strip()
                        if emp_id:
                            employee_id = emp_id
                    
                    # Ajouter à la liste des employés présents dans LDAP
                    ldap_employee_ids.add(employee_id)

                    if dry_run:
                        self.stdout.write(
                            f"  [DRY-RUN] {first_name} {last_name} ({email}) - {department_name}"
                        )
                        continue

                    try:
                        # Gérer le département
                        department, dept_created = Department.objects.get_or_create(
                            name=department_name,
                            defaults={'name': department_name}
                        )

                        # Créer ou mettre à jour l'employé (réactiver si nécessaire)
                        employee, employee_created = Employee.objects.update_or_create(
                            employee_id=employee_id,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'position_title': position_title,
                                'department': department,
                                'phone_fixed': phone_fixed or None,
                                'phone_mobile': phone_mobile or None,
                                'is_active': True,  # Toujours actif s'il est dans LDAP
                            }
                        )

                        # Synchroniser l'avatar si disponible
                        if sync_avatars and hasattr(entry, 'thumbnailPhoto') and entry.thumbnailPhoto:
                            try:
                                # ldap3 retourne thumbnailPhoto comme bytes
                                photo_data = bytes(entry.thumbnailPhoto)
                                if photo_data:
                                    # Mettre à jour l'avatar même s'il existe déjà (pour synchroniser les changements)
                                    employee.avatar.save(
                                        f"{sam}.jpg",
                                        ContentFile(photo_data),
                                        save=True
                                    )
                                    if not employee_created:  # Ne loguer que si mis à jour, pas créé
                                        self.stdout.write(f"  📸 Photo synchronisée pour {first_name} {last_name}")
                            except Exception as e:
                                logger.warning(f"Erreur lors de la synchronisation de la photo pour {sam}: {e}")

                        if employee_created:
                            created += 1
                            self.stdout.write(f"  ✅ Créé: {first_name} {last_name} ({department_name})")
                        else:
                            updated += 1
                            self.stdout.write(f"  🔄 Mis à jour: {first_name} {last_name} ({department_name})")
                    except Exception as e:
                        skipped += 1
                        error_msg = f"Erreur pour {sam}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                        
                except Exception as e:
                    skipped += 1
                    error_msg = f"Erreur lors du traitement de l'entrée: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue

            # Désactiver les employés qui ne sont plus dans LDAP (soft delete)
            if not dry_run:
                deactivated_qs = Employee.objects.filter(is_active=True).exclude(employee_id__in=ldap_employee_ids)
                deactivated = deactivated_qs.count()
                if deactivated > 0:
                    deactivated_qs.update(is_active=False)
                    self.stdout.write(f"  ⚠️  {deactivated} employé(s) désactivé(s) (supprimé(s) du LDAP)")

        conn.unbind()

        # Résumé
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"✅ Synchronisation terminée !"))
        self.stdout.write(self.style.SUCCESS(f"   📊 {created} employé(s) créé(s)"))
        self.stdout.write(self.style.SUCCESS(f"   🔄 {updated} employé(s) mis à jour"))
        if deactivated > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️  {deactivated} employé(s) désactivé(s)"))
        self.stdout.write(self.style.WARNING(f"   ⏭️  {skipped} employé(s) ignoré(s)"))
        if errors:
            self.stdout.write(self.style.ERROR(f"   ❌ {len(errors)} erreur(s)"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if errors and self.verbosity >= 2:
            self.stdout.write("\nErreurs détaillées:")
            for error in errors[:10]:  # Limiter à 10 erreurs
                self.stdout.write(self.style.ERROR(f"  - {error}"))
