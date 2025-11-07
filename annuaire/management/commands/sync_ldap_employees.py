"""
Management command pour synchroniser les employés depuis LDAP Active Directory
Usage: python manage.py sync_ldap_employees
"""
from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
from annuaire.models import Employee, Department
from django.contrib.auth import get_user_model
from decouple import config
import logging

User = get_user_model()

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
            # Pour les attributs binaires, on utilise auto_encode=True (par défaut) et on accède via conn.response
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
            'ipPhone',             # Téléphone fixe (corrigé: ipPhone = téléphone fixe)
            'telephoneNumber',     # Téléphone personnel (corrigé: telephoneNumber = téléphone personnel)
            'mobile',              # Téléphone mobile alternatif (si disponible)
            'title',               # Titre du poste (position)
            'department',          # Département (si disponible dans attribut)
            'sAMAccountName',      # Nom d'utilisateur Windows
            'employeeID',          # Matricule (si disponible - généralement absent)
            'employeeNumber',      # Numéro employé alternatif (si disponible)
            'thumbnailPhoto',      # Photo de profil
            'displayName',         # Nom d'affichage
            'distinguishedName',   # DN complet pour extraire le département depuis OU
            'manager',             # Manager (N+1) - DN du manager
        ]

        try:
            self.stdout.write(f"🔍 Recherche des utilisateurs dans {ldap_base_dn}...")
            self.stdout.write(f"🔍 Attributs recherchés: {', '.join(attrs)}")
            
            # Recherche LDAP avec récupération explicite des attributs
            # Pour les attributs binaires comme thumbnailPhoto, on récupère via conn.response
            conn.search(
                search_base=ldap_base_dn,
                search_filter=filterstr,
                search_scope=SUBTREE,
                attributes=attrs,
                get_operational_attributes=False
            )
            results = conn.entries
            # Garder une référence à conn.response pour accéder aux données binaires brutes
            # Structure: {dn: response_dict} pour accès rapide
            ldap_responses = {}
            for response in conn.response:
                if 'dn' in response and 'attributes' in response:
                    ldap_responses[response['dn']] = response
            
            # Collecter tous les départements uniques depuis les DN
            all_departments_from_dn = set()
            for entry in results:
                entry_dn = None
                if hasattr(entry, 'distinguishedName') and entry.distinguishedName:
                    entry_dn = str(entry.distinguishedName)
                elif hasattr(entry, 'entry_dn'):
                    entry_dn = str(entry.entry_dn)
                elif hasattr(entry, 'dn'):
                    entry_dn = str(entry.dn)
                
                if entry_dn:
                    try:
                        dn_parts = entry_dn.split(',')
                        for part in dn_parts:
                            part = part.strip()
                            if part.startswith('OU='):
                                ou_name = part[3:].strip()
                                generic_ous = ['Utilisateurs', 'UsersWifi', 'Users', 'Computers', 'Groups', 'Domain Controllers']
                                if ou_name not in generic_ous:
                                    all_departments_from_dn.add(ou_name)
                    except Exception:
                        pass
            
            self.stdout.write(self.style.SUCCESS(f"✅ {len(results)} utilisateurs trouvés dans LDAP"))
            if all_departments_from_dn:
                self.stdout.write(f"📁 {len(all_departments_from_dn)} département(s) unique(s) détecté(s) depuis les DN: {', '.join(sorted(all_departments_from_dn)[:10])}{'...' if len(all_departments_from_dn) > 10 else ''}")
            
            # Vérification détaillée pour thumbnailPhoto
            if results and sync_avatars:
                self.stdout.write(f"🔍 Vérification de thumbnailPhoto dans les résultats...")
                entries_with_photo = 0
                sample_with_photo = None
                
                for idx, entry in enumerate(results[:10]):  # Vérifier les 10 premiers
                    sam_name = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else f"entry_{idx}"
                    
                    # Vérifier toutes les méthodes d'accès
                    has_photo = False
                    access_method = None
                    
                    # Méthode 1: property directe (RECOMMANDÉ)
                    if hasattr(entry, 'thumbnailPhoto'):
                        try:
                            thumb_attr = entry.thumbnailPhoto
                            if thumb_attr is not None:
                                # Vérifier si c'est un objet Attribute ou directement la valeur
                                if hasattr(thumb_attr, 'value') or hasattr(thumb_attr, 'values') or isinstance(thumb_attr, (bytes, list)):
                                    has_photo = True
                                    access_method = "property"
                        except:
                            pass
                    
                    # Méthode 2: indexation
                    if not has_photo:
                        try:
                            if 'thumbnailPhoto' in entry:
                                has_photo = True
                                access_method = "indexation"
                        except:
                            pass
                    
                    # Méthode 3: entry_attributes (dict ou list)
                    if not has_photo and hasattr(entry, 'entry_attributes') and entry.entry_attributes:
                        try:
                            if isinstance(entry.entry_attributes, dict):
                                if 'thumbnailPhoto' in entry.entry_attributes:
                                    has_photo = True
                                    access_method = "entry_attributes_dict"
                            elif isinstance(entry.entry_attributes, list):
                                # Chercher dans la liste de tuples
                                for attr_name, attr_value in entry.entry_attributes:
                                    if attr_name == 'thumbnailPhoto':
                                        has_photo = True
                                        access_method = "entry_attributes_list"
                                        break
                        except:
                            pass
                    
                    if has_photo:
                        entries_with_photo += 1
                        if not sample_with_photo:
                            sample_with_photo = entry
                            self.stdout.write(f"🔍 Exemple: thumbnailPhoto trouvé pour {sam_name} (méthode: {access_method})")
                    
                    # Log spécial pour fgueye
                    if sam_name.lower() == 'fgueye':
                        self.stdout.write(f"🔍 [DEBUG fgueye] Vérification dans les résultats...")
                        self.stdout.write(f"  🔍 [DEBUG fgueye] has_photo: {has_photo}")
                        self.stdout.write(f"  🔍 [DEBUG fgueye] access_method: {access_method}")
                        if has_photo:
                            self.stdout.write(f"  ✅ [DEBUG fgueye] thumbnailPhoto PRÉSENT dans les résultats LDAP!")
                
                if entries_with_photo > 0:
                    self.stdout.write(f"🔍 {entries_with_photo} entrée(s) avec thumbnailPhoto trouvée(s) sur les {min(10, len(results))} premières")
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Aucun thumbnailPhoto trouvé dans les {min(10, len(results))} premiers résultats"))
                    self.stdout.write(self.style.WARNING("⚠️  Vérifiez que l'attribut thumbnailPhoto existe bien dans LDAP pour ces utilisateurs"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Échec recherche LDAP: {e}"))
            conn.unbind()
            return

        created = 0
        updated = 0
        skipped = 0
        deactivated = 0
        errors = []
        ldap_emails = set()  # Pour tracker les employés présents dans LDAP (par email)

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
                    
                    # Récupérer le DN pour extraire le département depuis les OU
                    entry_dn = None
                    if hasattr(entry, 'distinguishedName') and entry.distinguishedName:
                        entry_dn = str(entry.distinguishedName)
                    elif hasattr(entry, 'entry_dn'):
                        entry_dn = str(entry.entry_dn)
                    elif hasattr(entry, 'dn'):
                        entry_dn = str(entry.dn)
                    
                    # Département - PRIORITÉ: Extraire depuis le DN (OU) plutôt que depuis l'attribut department
                    department_name = ''
                    
                    # Méthode 1: Extraire depuis distinguishedName (OU)
                    if entry_dn:
                        # Parser le DN pour extraire les OU
                        # Format: CN=Nom,OU=Utilisateurs,OU=Département,OU=UsersWifi,DC=sar,DC=sn
                        # On veut extraire la partie OU qui représente le département (généralement la 2ème OU)
                        try:
                            dn_parts = entry_dn.split(',')
                            ou_parts = []
                            generic_ous = ['Utilisateurs', 'UsersWifi', 'Users', 'Computers', 'Groups', 'Domain Controllers']
                            
                            for part in dn_parts:
                                part = part.strip()
                                if part.startswith('OU='):
                                    ou_name = part[3:].strip()  # Enlever "OU="
                                    # Ignorer les OU génériques comme "Utilisateurs", "UsersWifi", etc.
                                    if ou_name not in generic_ous:
                                        ou_parts.append(ou_name)
                            
                            # Prendre la première OU non générique (généralement le département/service)
                            # Exemple: CN=Moustapha MBAYE,OU=Utilisateurs,OU=Informatique,OU=UsersWifi,DC=sar,DC=sn
                            # → département = "Informatique"
                            if ou_parts:
                                # Prendre la première OU non générique trouvée
                                department_name = ou_parts[0].strip()
                            else:
                                # Si aucune OU non générique trouvée, essayer la dernière OU (sauf si générique)
                                all_ous = [part[3:].strip() for part in dn_parts if part.strip().startswith('OU=')]
                                if all_ous:
                                    # Prendre la dernière OU qui n'est pas générique
                                    for ou in reversed(all_ous):
                                        if ou not in generic_ous:
                                            department_name = ou.strip()
                                            break
                        except Exception as e:
                            logger.debug(f"Erreur extraction département depuis DN {entry_dn}: {e}")
                    
                    # Méthode 2: Fallback - utiliser l'attribut department si disponible
                    if not department_name and hasattr(entry, 'department') and entry.department:
                        department_name = str(entry.department).strip()
                    
                    # Méthode 3: Fallback final
                    if not department_name:
                        department_name = 'Non affecté'
                    
                    # Téléphones - CORRIGÉ selon les spécifications
                    # ipPhone = téléphone fixe (bureau)
                    phone_fixed = ''
                    if hasattr(entry, 'ipPhone') and entry.ipPhone:
                        phone_fixed = str(entry.ipPhone).strip()
                    # Fallback: otherTelephone si ipPhone n'est pas disponible
                    if not phone_fixed and hasattr(entry, 'otherTelephone') and entry.otherTelephone:
                        phone_fixed = str(entry.otherTelephone).strip()
                    
                    # telephoneNumber = téléphone personnel (mobile)
                    phone_mobile = ''
                    if hasattr(entry, 'telephoneNumber') and entry.telephoneNumber:
                        phone_mobile = str(entry.telephoneNumber).strip()
                    # Fallback: mobile si telephoneNumber n'est pas disponible
                    if not phone_mobile and hasattr(entry, 'mobile') and entry.mobile:
                        phone_mobile = str(entry.mobile).strip()
                    
                    # L'email est utilisé comme identifiant unique (pas de matricule)
                    # Ajouter à la liste des employés présents dans LDAP
                    ldap_emails.add(email.lower())

                    if dry_run:
                        self.stdout.write(
                            f"  [DRY-RUN] {first_name} {last_name} ({email}) - {department_name}"
                        )
                        continue

                    try:
                        # entry_dn a déjà été récupéré plus haut pour l'extraction du département
                        # On le réutilise ici pour la gestion de l'avatar
                        
                        # Gérer le département - Créer tous les départements uniques détectés
                        department, dept_created = Department.objects.get_or_create(
                            name=department_name,
                            defaults={'name': department_name}
                        )
                        if dept_created:
                            self.stdout.write(f"  📁 Nouveau département créé: {department_name}")

                        # Créer ou mettre à jour l'employé (réactiver si nécessaire)
                        # Utiliser l'email comme identifiant unique (pas de matricule)
                        employee, employee_created = Employee.objects.update_or_create(
                            email=email,
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
                        if sync_avatars:
                            try:
                                photo_data = None
                                photo_data_raw = None
                                extraction_method = None
                                
                                # Log détaillé pour debug (surtout pour fgueye)
                                is_fgueye = sam.lower() == 'fgueye'
                                
                                # MÉTHODE PRINCIPALE: Recherche individuelle pour récupérer thumbnailPhoto
                                # ldap3 ne charge pas toujours les attributs binaires dans une recherche groupée
                                # Il faut faire une recherche séparée pour chaque utilisateur qui a thumbnailPhoto
                                # Faire la recherche individuelle si entry.thumbnailPhoto existe (même s'il est vide)
                                if hasattr(entry, 'thumbnailPhoto') and entry_dn:
                                    try:
                                        if is_fgueye:
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] Recherche individuelle pour thumbnailPhoto...")
                                        
                                        # Recherche individuelle pour cet utilisateur avec seulement thumbnailPhoto
                                        conn.search(
                                            search_base=entry_dn,
                                            search_filter='(objectClass=*)',
                                            search_scope=SUBTREE,
                                            attributes=['thumbnailPhoto'],
                                            get_operational_attributes=False
                                        )
                                        
                                        # Récupérer depuis la nouvelle réponse
                                        if conn.response:
                                            for resp in conn.response:
                                                if 'dn' in resp and resp['dn'].lower() == entry_dn.lower():
                                                    if is_fgueye:
                                                        self.stdout.write(f"  🔍 [DEBUG fgueye] Réponse individuelle trouvée, keys: {list(resp.keys())}")
                                                    
                                                    # PRIORITÉ 1: Essayer raw_attributes d'abord (données binaires brutes)
                                                    if 'raw_attributes' in resp and isinstance(resp['raw_attributes'], dict):
                                                        raw_attrs = resp['raw_attributes']
                                                        if is_fgueye:
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] raw_attributes keys: {list(raw_attrs.keys())}")
                                                        
                                                        # Chercher thumbnailPhoto (case-insensitive)
                                                        for key in raw_attrs.keys():
                                                            if key.lower() == 'thumbnailphoto':
                                                                thumb_data = raw_attrs[key]
                                                                if is_fgueye:
                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] thumbnailPhoto trouvé dans raw_attributes, type: {type(thumb_data)}")
                                                                
                                                                if thumb_data:
                                                                    if isinstance(thumb_data, list) and len(thumb_data) > 0:
                                                                        if isinstance(thumb_data[0], bytes):
                                                                            photo_data_raw = thumb_data[0]
                                                                            extraction_method = "individual_search_raw_list"
                                                                            if is_fgueye:
                                                                                self.stdout.write(f"  ✅ [DEBUG fgueye] SUCCESS (raw_list): taille={len(photo_data_raw)} bytes")
                                                                            break
                                                                        else:
                                                                            try:
                                                                                photo_data_raw = bytes(thumb_data[0])
                                                                                extraction_method = "individual_search_raw_list_converted"
                                                                                if is_fgueye:
                                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] SUCCESS (raw_list converted): taille={len(photo_data_raw)} bytes")
                                                                                break
                                                                            except Exception as conv_err:
                                                                                if is_fgueye:
                                                                                    self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur conversion: {conv_err}")
                                                                    elif isinstance(thumb_data, bytes):
                                                                        photo_data_raw = thumb_data
                                                                        extraction_method = "individual_search_raw_bytes"
                                                                        if is_fgueye:
                                                                            self.stdout.write(f"  ✅ [DEBUG fgueye] SUCCESS (raw_bytes): taille={len(photo_data_raw)} bytes")
                                                                        break
                                                                break
                                                        
                                                        # Si pas encore trouvé, essayer l'accès direct
                                                        if not photo_data_raw and 'thumbnailPhoto' in raw_attrs:
                                                            thumb_data = raw_attrs['thumbnailPhoto']
                                                            if thumb_data and isinstance(thumb_data, list) and len(thumb_data) > 0:
                                                                if isinstance(thumb_data[0], bytes):
                                                                    photo_data_raw = thumb_data[0]
                                                                    extraction_method = "individual_search_raw_direct"
                                                                    if is_fgueye:
                                                                        self.stdout.write(f"  ✅ [DEBUG fgueye] SUCCESS (raw_direct): taille={len(photo_data_raw)} bytes")
                                                    
                                                    # PRIORITÉ 2: Fallback - essayer attributes
                                                    if not photo_data_raw and 'attributes' in resp and isinstance(resp['attributes'], dict):
                                                        attrs = resp['attributes']
                                                        if is_fgueye:
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] Essai avec attributes, keys: {list(attrs.keys())[:10]}")
                                                        
                                                        for key in attrs.keys():
                                                            if key.lower() == 'thumbnailphoto':
                                                                thumb_data = attrs[key]
                                                                if thumb_data and isinstance(thumb_data, list) and len(thumb_data) > 0:
                                                                    if isinstance(thumb_data[0], bytes):
                                                                        photo_data_raw = thumb_data[0]
                                                                        extraction_method = "individual_search_attrs_list"
                                                                        if is_fgueye:
                                                                            self.stdout.write(f"  ✅ [DEBUG fgueye] SUCCESS (attrs_list): taille={len(photo_data_raw)} bytes")
                                                                        break
                                                    break
                                        
                                        if not photo_data_raw and is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Recherche individuelle n'a pas trouvé thumbnailPhoto")
                                            
                                    except Exception as individual_search_error:
                                        if is_fgueye:
                                            self.stdout.write(f"  ❌ [DEBUG fgueye] Erreur recherche individuelle: {individual_search_error}")
                                            import traceback
                                            self.stdout.write(f"  ❌ [DEBUG fgueye] Traceback: {traceback.format_exc()}")
                                        logger.debug(f"Erreur recherche individuelle thumbnailPhoto pour {sam}: {individual_search_error}")
                                
                                if is_fgueye:
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] Recherche thumbnailPhoto...")
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] entry type: {type(entry)}")
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] entry_dn: {entry_dn}")
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] ldap_responses keys (first 5): {list(ldap_responses.keys())[:5] if ldap_responses else 'EMPTY'}")
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] hasattr entry_attributes: {hasattr(entry, 'entry_attributes')}")
                                    if hasattr(entry, 'entry_attributes') and entry.entry_attributes:
                                        if isinstance(entry.entry_attributes, dict):
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] entry_attributes type: dict, keys: {list(entry.entry_attributes.keys())}")
                                        elif isinstance(entry.entry_attributes, list):
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] entry_attributes type: list, length: {len(entry.entry_attributes)}")
                                            # Afficher les noms d'attributs dans la liste
                                            attr_names = []
                                            try:
                                                for item in entry.entry_attributes[:5]:  # Premiers 5
                                                    if isinstance(item, tuple) and len(item) >= 2:
                                                        attr_names.append(str(item[0]))
                                                    elif isinstance(item, dict):
                                                        attr_names.extend(item.keys())
                                            except:
                                                pass
                                            if attr_names:
                                                self.stdout.write(f"  🔍 [DEBUG fgueye] entry_attributes sample attributes: {attr_names}")
                                        else:
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] entry_attributes type: {type(entry.entry_attributes)}")
                                    self.stdout.write(f"  🔍 [DEBUG fgueye] hasattr thumbnailPhoto: {hasattr(entry, 'thumbnailPhoto')}")
                                    if hasattr(entry, 'thumbnailPhoto'):
                                        try:
                                            thumb_attr = entry.thumbnailPhoto
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto value type: {type(thumb_attr)}")
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto is None: {thumb_attr is None}")
                                            if thumb_attr is not None:
                                                if hasattr(thumb_attr, 'raw_values'):
                                                    raw_vals = thumb_attr.raw_values
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto has .raw_values, type: {type(raw_vals)}, is_empty: {not raw_vals if raw_vals else True}")
                                                    if raw_vals:
                                                        if isinstance(raw_vals, list):
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] raw_values is list, length: {len(raw_vals)}")
                                                        elif isinstance(raw_vals, bytes):
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] raw_values is bytes, length: {len(raw_vals)}")
                                                if hasattr(thumb_attr, 'value'):
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto has .value, type: {type(thumb_attr.value)}")
                                                if hasattr(thumb_attr, 'values'):
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto has .values, length: {len(thumb_attr.values) if thumb_attr.values else 0}")
                                                if hasattr(thumb_attr, '__len__'):
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto length: {len(thumb_attr)}")
                                        except Exception as e:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur inspection thumbnailPhoto: {e}")
                                
                                # Méthode 1: Accès via propriété directe entry.thumbnailPhoto (RECOMMANDÉ avec ldap3)
                                # Pour les attributs binaires, ldap3 utilise .raw_values (bytes) au lieu de .values (décodé)
                                if hasattr(entry, 'thumbnailPhoto'):
                                    try:
                                        thumb_attr = entry.thumbnailPhoto
                                        if thumb_attr is not None:
                                            # PRIORITÉ 1: .raw_values pour les attributs binaires (bytes bruts)
                                            if hasattr(thumb_attr, 'raw_values') and thumb_attr.raw_values:
                                                if isinstance(thumb_attr.raw_values, list) and len(thumb_attr.raw_values) > 0:
                                                    photo_data_raw = thumb_attr.raw_values[0]
                                                    extraction_method = "property_raw_values"
                                                elif isinstance(thumb_attr.raw_values, bytes):
                                                    photo_data_raw = thumb_attr.raw_values
                                                    extraction_method = "property_raw_values_bytes"
                                            # PRIORITÉ 2: .value si c'est directement bytes
                                            elif hasattr(thumb_attr, 'value') and thumb_attr.value is not None:
                                                if isinstance(thumb_attr.value, bytes):
                                                    photo_data_raw = thumb_attr.value
                                                    extraction_method = "property_value_bytes"
                                            # PRIORITÉ 3: .values si disponible
                                            elif hasattr(thumb_attr, 'values') and thumb_attr.values:
                                                if isinstance(thumb_attr.values, list) and len(thumb_attr.values) > 0:
                                                    photo_data_raw = thumb_attr.values[0]
                                                    extraction_method = "property_values"
                                            # PRIORITÉ 4: Directement bytes
                                            elif isinstance(thumb_attr, bytes):
                                                photo_data_raw = thumb_attr
                                                extraction_method = "property_bytes"
                                            
                                            if is_fgueye:
                                                self.stdout.write(f"  🔍 [DEBUG fgueye] Méthode 1: Trouvé via property ({extraction_method}), type: {type(photo_data_raw)}, has_raw_values: {hasattr(thumb_attr, 'raw_values') if thumb_attr else False}")
                                                if hasattr(thumb_attr, 'raw_values'):
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] raw_values type: {type(thumb_attr.raw_values)}, length: {len(thumb_attr.raw_values) if isinstance(thumb_attr.raw_values, (list, bytes)) else 'N/A'}")
                                    except Exception as e:
                                        if is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur méthode 1: {e}")
                                        logger.debug(f"Erreur méthode 1 pour {sam}: {e}")
                                
                                # Méthode 2: Accès via indexation entry['thumbnailPhoto']
                                if not photo_data_raw:
                                    try:
                                        if 'thumbnailPhoto' in entry:
                                            thumb_attr = entry['thumbnailPhoto']
                                            if thumb_attr is not None:
                                                # PRIORITÉ 1: .raw_values pour les attributs binaires
                                                if hasattr(thumb_attr, 'raw_values') and thumb_attr.raw_values:
                                                    if isinstance(thumb_attr.raw_values, list) and len(thumb_attr.raw_values) > 0:
                                                        photo_data_raw = thumb_attr.raw_values[0]
                                                        extraction_method = "indexation_raw_values"
                                                    elif isinstance(thumb_attr.raw_values, bytes):
                                                        photo_data_raw = thumb_attr.raw_values
                                                        extraction_method = "indexation_raw_values_bytes"
                                                # PRIORITÉ 2: .value si c'est bytes
                                                elif hasattr(thumb_attr, 'value') and thumb_attr.value is not None:
                                                    if isinstance(thumb_attr.value, bytes):
                                                        photo_data_raw = thumb_attr.value
                                                        extraction_method = "indexation_value_bytes"
                                                # PRIORITÉ 3: .values
                                                elif hasattr(thumb_attr, 'values') and thumb_attr.values:
                                                    if isinstance(thumb_attr.values, list) and len(thumb_attr.values) > 0:
                                                        photo_data_raw = thumb_attr.values[0]
                                                        extraction_method = "indexation_values"
                                                # PRIORITÉ 4: Directement bytes
                                                elif isinstance(thumb_attr, bytes):
                                                    photo_data_raw = thumb_attr
                                                    extraction_method = "indexation_bytes"
                                                
                                                if is_fgueye:
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] Méthode 2: Trouvé via indexation ({extraction_method}), type: {type(photo_data_raw)}")
                                    except (KeyError, TypeError, AttributeError) as e:
                                        if is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur méthode 2: {e}")
                                        logger.debug(f"Erreur méthode 2 pour {sam}: {e}")
                                
                                # Méthode 3: Accès via conn.response (MÉTHODE LA PLUS FIABLE pour les attributs binaires)
                                if not photo_data_raw:
                                    if is_fgueye:
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] Tentative Méthode 3 (conn.response)...")
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] entry_dn: {entry_dn}")
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] ldap_responses count: {len(ldap_responses)}")
                                    
                                    if entry_dn:
                                        try:
                                            # Chercher dans ldap_responses par DN
                                            response_data = None
                                            for resp_dn, resp_dict in ldap_responses.items():
                                                # Comparer les DN (peuvent être normalisés différemment)
                                                if resp_dn.lower() == entry_dn.lower() or resp_dn == entry_dn:
                                                    response_data = resp_dict
                                                    if is_fgueye:
                                                        self.stdout.write(f"  🔍 [DEBUG fgueye] DN trouvé: {resp_dn}")
                                                    break
                                            
                                            if is_fgueye and not response_data:
                                                self.stdout.write(f"  ⚠️ [DEBUG fgueye] Aucun DN correspondant trouvé dans ldap_responses")
                                            
                                            if response_data:
                                                if is_fgueye:
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] response_data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'NOT DICT'}")
                                                
                                                # PRIORITÉ: Utiliser raw_attributes pour les données binaires (bytes bruts)
                                                if 'raw_attributes' in response_data:
                                                    raw_attrs = response_data['raw_attributes']
                                                    if is_fgueye:
                                                        self.stdout.write(f"  🔍 [DEBUG fgueye] raw_attributes type: {type(raw_attrs)}")
                                                        if isinstance(raw_attrs, dict):
                                                            all_keys = list(raw_attrs.keys())
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] raw_attributes keys (all): {all_keys}")
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] raw_attributes keys count: {len(all_keys)}")
                                                            # Vérifier toutes les variations possibles du nom
                                                            thumbnail_variations = ['thumbnailPhoto', 'thumbnailphoto', 'THUMBNAILPHOTO', 'jpegPhoto', 'photo']
                                                            for var in thumbnail_variations:
                                                                if var in raw_attrs:
                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] Trouvé variation: {var}")
                                                    
                                                    # Essayer avec toutes les variations possibles du nom (case-insensitive)
                                                    thumbnail_found = False
                                                    if isinstance(raw_attrs, dict):
                                                        # CaseInsensitiveDict supporte l'accès case-insensitive
                                                        for key in raw_attrs.keys():
                                                            if key.lower() == 'thumbnailphoto' or key.lower() == 'jpegphoto':
                                                                thumbnail_found = True
                                                                thumb_data = raw_attrs[key]
                                                                if is_fgueye:
                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] thumbnailPhoto trouvé avec clé: {key}, type: {type(thumb_data)}")
                                                                break
                                                    
                                                    if thumbnail_found:
                                                        thumb_data = raw_attrs.get('thumbnailPhoto') or raw_attrs.get('thumbnailphoto') or raw_attrs.get('THUMBNAILPHOTO')
                                                        if not thumb_data:
                                                            # Essayer de trouver avec la clé exacte trouvée
                                                            for key in raw_attrs.keys():
                                                                if key.lower() == 'thumbnailphoto':
                                                                    thumb_data = raw_attrs[key]
                                                                    break
                                                    
                                                    if not thumbnail_found and isinstance(raw_attrs, dict) and 'thumbnailPhoto' in raw_attrs:
                                                        thumb_data = raw_attrs['thumbnailPhoto']
                                                        if is_fgueye:
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto trouvé dans raw_attributes (direct), type: {type(thumb_data)}")
                                                    
                                                    if thumbnail_found or (isinstance(raw_attrs, dict) and 'thumbnailPhoto' in raw_attrs):
                                                        if not thumb_data:
                                                            thumb_data = raw_attrs.get('thumbnailPhoto') or next((raw_attrs[k] for k in raw_attrs.keys() if k.lower() == 'thumbnailphoto'), None)
                                                        if thumb_data:
                                                            if is_fgueye:
                                                                self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto trouvé dans raw_attributes, type: {type(thumb_data)}")
                                                            # thumb_data peut être une liste de bytes ou directement bytes
                                                            if isinstance(thumb_data, list) and len(thumb_data) > 0:
                                                                first_item = thumb_data[0]
                                                                if isinstance(first_item, bytes):
                                                                    photo_data_raw = first_item
                                                                    extraction_method = "conn_response_list"
                                                                    if is_fgueye:
                                                                        self.stdout.write(f"  ✅ [DEBUG fgueye] Méthode 3 SUCCESS (list): taille={len(photo_data_raw)}")
                                                                else:
                                                                    try:
                                                                        photo_data_raw = bytes(first_item)
                                                                        extraction_method = "conn_response_list_converted"
                                                                        if is_fgueye:
                                                                            self.stdout.write(f"  ✅ [DEBUG fgueye] Méthode 3 SUCCESS (list converted): taille={len(photo_data_raw)}")
                                                                    except Exception as conv_err:
                                                                        if is_fgueye:
                                                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur conversion bytes: {conv_err}")
                                                            elif isinstance(thumb_data, bytes):
                                                                photo_data_raw = thumb_data
                                                                extraction_method = "conn_response_bytes"
                                                                if is_fgueye:
                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] Méthode 3 SUCCESS (bytes direct): taille={len(photo_data_raw)}")
                                                            else:
                                                                if is_fgueye:
                                                                    self.stdout.write(f"  ⚠️ [DEBUG fgueye] thumbnailPhoto type inconnu: {type(thumb_data)}")
                                                        else:
                                                            if is_fgueye:
                                                                self.stdout.write(f"  ⚠️ [DEBUG fgueye] thumbnailPhoto est vide/None")
                                                    else:
                                                        if is_fgueye:
                                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] thumbnailPhoto PAS dans raw_attributes")
                                                
                                                # FALLBACK: Essayer aussi dans attributes (si raw_attributes n'a pas fonctionné)
                                                if not photo_data_raw and 'attributes' in response_data:
                                                    attrs_dict = response_data['attributes']
                                                    if is_fgueye:
                                                        self.stdout.write(f"  🔍 [DEBUG fgueye] FALLBACK: Essai avec attributes, type: {type(attrs_dict)}")
                                                    
                                                    # attributes peut être une liste de tuples ou un dict
                                                    if isinstance(attrs_dict, dict) and 'thumbnailPhoto' in attrs_dict:
                                                        thumb_data = attrs_dict['thumbnailPhoto']
                                                        if is_fgueye:
                                                            self.stdout.write(f"  🔍 [DEBUG fgueye] thumbnailPhoto trouvé dans attributes (dict), type: {type(thumb_data)}")
                                                        if thumb_data and isinstance(thumb_data, list) and len(thumb_data) > 0:
                                                            first_item = thumb_data[0]
                                                            if isinstance(first_item, bytes):
                                                                photo_data_raw = first_item
                                                                extraction_method = "attributes_fallback_list"
                                                                if is_fgueye:
                                                                    self.stdout.write(f"  ✅ [DEBUG fgueye] FALLBACK SUCCESS: taille={len(photo_data_raw)}")
                                                    elif isinstance(attrs_dict, list):
                                                        # Chercher thumbnailPhoto dans la liste
                                                        for attr_item in attrs_dict:
                                                            if isinstance(attr_item, tuple) and len(attr_item) >= 2:
                                                                attr_name, attr_value = attr_item[0], attr_item[1]
                                                                if attr_name == 'thumbnailPhoto' and attr_value:
                                                                    if isinstance(attr_value, bytes):
                                                                        photo_data_raw = attr_value
                                                                        extraction_method = "attributes_fallback_list_tuple"
                                                                        if is_fgueye:
                                                                            self.stdout.write(f"  ✅ [DEBUG fgueye] FALLBACK SUCCESS (list tuple): taille={len(photo_data_raw)}")
                                                                        break
                                                
                                                if not photo_data_raw:
                                                    if is_fgueye:
                                                        self.stdout.write(f"  ⚠️ [DEBUG fgueye] Aucune méthode n'a réussi à récupérer thumbnailPhoto")
                                        except Exception as e:
                                            if is_fgueye:
                                                self.stdout.write(f"  ❌ [DEBUG fgueye] Erreur méthode 3 (conn.response): {e}")
                                                import traceback
                                                self.stdout.write(f"  ❌ [DEBUG fgueye] Traceback: {traceback.format_exc()}")
                                            logger.debug(f"Erreur méthode 3 (conn.response) pour {sam}: {e}")
                                    else:
                                        if is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] entry_dn est None, impossible d'utiliser conn.response")
                                
                                # Méthode 4: Accès via entry_attributes (si c'est un dict, pas une liste)
                                if not photo_data_raw and hasattr(entry, 'entry_attributes'):
                                    try:
                                        # entry_attributes peut être un dict ou une liste selon la version de ldap3
                                        if isinstance(entry.entry_attributes, dict):
                                            if 'thumbnailPhoto' in entry.entry_attributes:
                                                photo_data_raw = entry.entry_attributes['thumbnailPhoto']
                                                extraction_method = "entry_attributes_dict"
                                                if is_fgueye:
                                                    self.stdout.write(f"  🔍 [DEBUG fgueye] Méthode 3: Trouvé via entry_attributes (dict), type: {type(photo_data_raw)}")
                                        elif isinstance(entry.entry_attributes, list):
                                            # Si c'est une liste, chercher le tuple (attribut, valeur) ou dict
                                            for item in entry.entry_attributes:
                                                attr_name = None
                                                attr_value = None
                                                
                                                # Gérer les différents formats de liste
                                                if isinstance(item, tuple) and len(item) >= 2:
                                                    attr_name, attr_value = item[0], item[1]
                                                elif isinstance(item, dict):
                                                    if 'thumbnailPhoto' in item:
                                                        attr_name = 'thumbnailPhoto'
                                                        attr_value = item['thumbnailPhoto']
                                                elif isinstance(item, str) and item == 'thumbnailPhoto':
                                                    # Format spécial où le nom est dans la liste et la valeur est ailleurs
                                                    continue
                                                
                                                if attr_name == 'thumbnailPhoto' and attr_value is not None:
                                                    photo_data_raw = attr_value
                                                    extraction_method = "entry_attributes_list"
                                                    if is_fgueye:
                                                        self.stdout.write(f"  🔍 [DEBUG fgueye] Méthode 3: Trouvé via entry_attributes (list), type: {type(photo_data_raw)}")
                                                    break
                                    except Exception as e:
                                        if is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur méthode 3: {e}")
                                
                                # Conversion des données en bytes
                                if photo_data_raw is not None:
                                    if is_fgueye:
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] Conversion des données, type: {type(photo_data_raw)}")
                                    
                                    # ldap3 retourne généralement thumbnailPhoto comme une liste de bytes
                                    if isinstance(photo_data_raw, list) and len(photo_data_raw) > 0:
                                        if is_fgueye:
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] C'est une liste, longueur: {len(photo_data_raw)}")
                                        first_item = photo_data_raw[0]
                                        if first_item is not None:
                                            if isinstance(first_item, bytes):
                                                photo_data = first_item
                                            else:
                                                try:
                                                    photo_data = bytes(first_item)
                                                except Exception as e:
                                                    if is_fgueye:
                                                        self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur conversion bytes: {e}")
                                                    logger.debug(f"Erreur conversion bytes pour {sam}: {e}")
                                    elif isinstance(photo_data_raw, bytes):
                                        photo_data = photo_data_raw
                                        if is_fgueye:
                                            self.stdout.write(f"  🔍 [DEBUG fgueye] C'est déjà bytes, taille: {len(photo_data)}")
                                    elif isinstance(photo_data_raw, (str,)):
                                        try:
                                            photo_data = photo_data_raw.encode('latin-1')
                                            if is_fgueye:
                                                self.stdout.write(f"  🔍 [DEBUG fgueye] Converti depuis string, taille: {len(photo_data)}")
                                        except Exception as e:
                                            if is_fgueye:
                                                self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur conversion string: {e}")
                                            logger.debug(f"Erreur conversion string pour {sam}: {e}")
                                    else:
                                        try:
                                            photo_data = bytes(photo_data_raw)
                                            if is_fgueye:
                                                self.stdout.write(f"  🔍 [DEBUG fgueye] Converti depuis autre type, taille: {len(photo_data)}")
                                        except Exception as e:
                                            if is_fgueye:
                                                self.stdout.write(f"  ⚠️ [DEBUG fgueye] Erreur conversion autre type: {e}")
                                            logger.debug(f"Erreur conversion bytes pour {sam}: {e}")
                                
                                if is_fgueye:
                                    if photo_data:
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] photo_data obtenu, taille: {len(photo_data)} bytes")
                                    else:
                                        self.stdout.write(f"  ⚠️ [DEBUG fgueye] photo_data est None ou vide")
                                
                                # Validation et sauvegarde
                                if photo_data and len(photo_data) > 100:  # Au moins 100 bytes pour être une vraie image
                                    # Vérifier que c'est bien une image (JPEG/PNG/GIF)
                                    is_valid_image = (
                                        (len(photo_data) >= 2 and photo_data[:2] == b'\xff\xd8') or  # JPEG
                                        (len(photo_data) >= 8 and photo_data[:8] == b'\x89PNG\r\n\x1a\n') or  # PNG
                                        (len(photo_data) >= 4 and photo_data[:4] == b'GIF8')  # GIF
                                    )
                                    
                                    if is_fgueye:
                                        self.stdout.write(f"  🔍 [DEBUG fgueye] Validation image: is_valid={is_valid_image}, début: {photo_data[:10]}")
                                    
                                    if is_valid_image:
                                        # Toujours mettre à jour l'avatar (même s'il existe déjà) pour synchroniser les changements
                                        try:
                                            employee.avatar.save(
                                                f"avatars/{sam}.jpg",
                                                ContentFile(photo_data),
                                                save=True
                                            )
                                            self.stdout.write(f"  📸 Avatar synchronisé pour {first_name} {last_name} ({len(photo_data)} bytes, méthode: {extraction_method})")
                                            if is_fgueye:
                                                self.stdout.write(f"  ✅ [DEBUG fgueye] Avatar SAUVEGARDÉ avec succès!")
                                        except Exception as save_error:
                                            logger.error(f"Erreur lors de la sauvegarde de l'avatar pour {sam}: {save_error}")
                                            self.stdout.write(f"  ⚠️  Erreur sauvegarde avatar pour {first_name} {last_name}: {str(save_error)}")
                                            if is_fgueye:
                                                self.stdout.write(f"  ❌ [DEBUG fgueye] Erreur sauvegarde: {save_error}")
                                    else:
                                        logger.debug(f"Données photo invalides pour {sam} (pas une image valide, {len(photo_data)} bytes, début: {photo_data[:10]})")
                                        if is_fgueye:
                                            self.stdout.write(f"  ⚠️ [DEBUG fgueye] Image invalide (début: {photo_data[:20]})")
                                else:
                                    # Log détaillé si pas de données
                                    if is_fgueye:
                                        self.stdout.write(f"  ⚠️ [DEBUG fgueye] Pas de photo_data valide (photo_data={photo_data is not None}, taille={len(photo_data) if photo_data else 0})")
                                    elif 'thumbnailPhoto' in attrs:
                                        logger.debug(f"Pas de thumbnailPhoto valide pour {sam} (photo_data: {photo_data is not None}, taille: {len(photo_data) if photo_data else 0})")
                            except Exception as e:
                                logger.error(f"Erreur lors de la synchronisation de la photo pour {sam}: {e}", exc_info=True)
                                self.stdout.write(f"  ⚠️  Erreur avatar pour {first_name} {last_name}: {str(e)}")
                                if sam.lower() == 'fgueye':
                                    self.stdout.write(f"  ❌ [DEBUG fgueye] Exception complète: {e}")
                                    import traceback
                                    self.stdout.write(f"  ❌ [DEBUG fgueye] Traceback: {traceback.format_exc()}")

                        # Synchroniser l'utilisateur Django (User) depuis LDAP
                        # Créer ou mettre à jour le compte User Django pour l'authentification
                        # IMPORTANT: Seulement si l'utilisateur a un email (obligatoire pour l'authentification)
                        if email:
                            try:
                                # Extraire les données LDAP pour le User Django
                                
                                # Poste occupé (position) = title dans LDAP
                                user_position = ''
                                if hasattr(entry, 'title') and entry.title:
                                    user_position = str(entry.title).strip()
                                
                                # Téléphone fixe = ipPhone dans LDAP
                                user_phone_fixed = phone_fixed  # Déjà extrait plus haut
                                
                                # Téléphone personnel = telephoneNumber dans LDAP
                                user_phone_number = phone_mobile  # telephoneNumber = téléphone personnel
                                
                                # Manager (N+1) - Extraire depuis le champ manager (DN)
                                user_manager = None
                                if hasattr(entry, 'manager') and entry.manager:
                                    manager_dn = str(entry.manager)
                                    # Chercher le manager dans LDAP pour obtenir son email
                                    try:
                                        # Rechercher le manager par son DN dans LDAP
                                        try:
                                            conn_mgr = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
                                            try:
                                                conn_mgr.search(
                                                    search_base=str(manager_dn),
                                                    search_filter='(objectClass=user)',
                                                    search_scope=SUBTREE,
                                                    attributes=['mail', 'userPrincipalName']
                                                )
                                            except Exception:
                                                # Si la recherche par DN direct échoue, chercher dans toute la base
                                                conn_mgr.search(
                                                    search_base=ldap_base_dn,
                                                    search_filter=f'(&(objectClass=user)(distinguishedName={manager_dn}))',
                                                    search_scope=SUBTREE,
                                                    attributes=['mail', 'userPrincipalName']
                                                )
                                            
                                            if conn_mgr.entries:
                                                manager_entry = conn_mgr.entries[0]
                                                manager_email = None
                                                if hasattr(manager_entry, 'mail') and manager_entry.mail:
                                                    manager_email = str(manager_entry.mail).strip()
                                                elif hasattr(manager_entry, 'userPrincipalName') and manager_entry.userPrincipalName:
                                                    manager_email = str(manager_entry.userPrincipalName).strip()
                                                
                                                if manager_email:
                                                    try:
                                                        user_manager = User.objects.get(email=manager_email)
                                                    except User.DoesNotExist:
                                                        pass
                                            
                                            conn_mgr.unbind()
                                        except Exception as ldap_mgr_error:
                                            logger.debug(f"Erreur recherche LDAP manager {manager_dn}: {ldap_mgr_error}")
                                        
                                        # Fallback: Chercher par le nom extrait du CN
                                        if not user_manager:
                                            dn_parts = manager_dn.split(',')
                                            cn_part = None
                                            for part in dn_parts:
                                                part = part.strip()
                                                if part.startswith('CN='):
                                                    cn_part = part[3:].strip()
                                                    break
                                            
                                            if cn_part:
                                                name_parts = cn_part.split()
                                                if len(name_parts) >= 2:
                                                    # Essayer "Prénom Nom"
                                                    user_manager = User.objects.filter(
                                                        first_name__iexact=name_parts[0],
                                                        last_name__iexact=' '.join(name_parts[1:])
                                                    ).first()
                                                    
                                                    # Essayer "Nom Prénom" si pas trouvé
                                                    if not user_manager:
                                                        user_manager = User.objects.filter(
                                                            first_name__iexact=' '.join(name_parts[:-1]),
                                                            last_name__iexact=name_parts[-1]
                                                        ).first()
                                    except Exception as mgr_error:
                                        logger.debug(f"Erreur lors de la recherche du manager depuis DN {manager_dn}: {mgr_error}")
                                
                                # Générer un username unique (email sans @ ou sam_account_name)
                                username = email.split('@')[0] if '@' in email else sam
                                base_username = username
                                counter = 1
                                while User.objects.filter(username=username).exclude(email=email).exists():
                                    username = f"{base_username}{counter}"
                                    counter += 1
                                
                                # Chercher l'utilisateur par email uniquement
                                # Le matricule n'existe pas dans LDAP et ne doit pas être utilisé
                                django_user = None
                                try:
                                    django_user = User.objects.get(email=email)
                                except User.DoesNotExist:
                                    pass
                                
                                if not django_user:
                                    # Créer un nouvel utilisateur Django avec tous les champs LDAP
                                    # Le champ matricule n'est PAS rempli car il n'existe pas dans LDAP
                                    # Il peut être renseigné manuellement dans l'admin Django
                                    django_user = User.objects.create_user(
                                        username=username,
                                        email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        position=user_position or None,
                                        phone_fixed=user_phone_fixed or None,
                                        phone_number=user_phone_number or None,
                                        department=department,
                                        manager=user_manager,
                                        # matricule non rempli - doit être renseigné manuellement si nécessaire
                                        is_active=True  # TOUJOURS actif pour les comptes LDAP avec email
                                    )
                                    # Définir un mot de passe non utilisable (authentification via LDAP uniquement)
                                    django_user.set_unusable_password()
                                    django_user.save()
                                    
                                    self.stdout.write(f"  👤 Compte utilisateur Django créé (actif): {email}")
                                else:
                                    # Mettre à jour l'utilisateur existant avec toutes les données LDAP
                                    # TOUJOURS activer les comptes LDAP avec email (même si aucun autre champ n'a changé)
                                    updated_user = False
                                    was_inactive = not django_user.is_active
                                    
                                    if django_user.email != email:
                                        django_user.email = email
                                        updated_user = True
                                    if django_user.first_name != first_name:
                                        django_user.first_name = first_name
                                        updated_user = True
                                    if django_user.last_name != last_name:
                                        django_user.last_name = last_name
                                        updated_user = True
                                    
                                    # Poste occupé (position) = title dans LDAP
                                    if django_user.position != user_position and user_position:
                                        django_user.position = user_position
                                        updated_user = True
                                    
                                    # Téléphone fixe = ipPhone dans LDAP
                                    if django_user.phone_fixed != user_phone_fixed and user_phone_fixed:
                                        django_user.phone_fixed = user_phone_fixed
                                        updated_user = True
                                    
                                    # Téléphone personnel = telephoneNumber dans LDAP
                                    if django_user.phone_number != user_phone_number and user_phone_number:
                                        django_user.phone_number = user_phone_number
                                        updated_user = True
                                    
                                    # Département - Extraire depuis distinguishedName (OU)
                                    if department and django_user.department != department:
                                        django_user.department = department
                                        updated_user = True
                                    
                                    # Manager (N+1) - Mettre à jour si différent
                                    if user_manager and django_user.manager != user_manager:
                                        django_user.manager = user_manager
                                        updated_user = True
                                    elif not user_manager and django_user.manager:
                                        # Si le manager n'est plus dans LDAP, le vider
                                        django_user.manager = None
                                        updated_user = True
                                    
                                    # Le matricule n'est PAS mis à jour automatiquement car il n'existe pas dans LDAP
                                    # Il doit être renseigné manuellement dans l'admin Django si nécessaire
                                    
                                    # IMPORTANT: TOUJOURS activer si le compte est dans LDAP avec un email
                                    # Même si aucun autre champ n'a changé, on doit s'assurer que l'utilisateur est actif
                                    if not django_user.is_active:
                                        django_user.is_active = True
                                        updated_user = True
                                        self.stdout.write(f"  👤 Compte utilisateur Django réactivé: {email}")
                                    
                                    # Sauvegarder si des modifications ont été apportées
                                    if updated_user:
                                        django_user.save()
                                        if was_inactive:
                                            self.stdout.write(f"  👤 Compte utilisateur Django réactivé et mis à jour: {email}")
                                        else:
                                            self.stdout.write(f"  👤 Compte utilisateur Django mis à jour: {email}")
                                    # Si aucun autre champ n'a changé mais que l'utilisateur était inactif, il a déjà été activé ci-dessus
                            except Exception as user_error:
                                logger.error(f"Erreur lors de la synchronisation de l'utilisateur Django pour {sam}: {user_error}")
                                import traceback
                                logger.error(traceback.format_exc())
                                self.stdout.write(f"  ⚠️  Erreur création utilisateur Django pour {first_name} {last_name}: {str(user_error)}")
                        
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
                deactivated_qs = Employee.objects.filter(is_active=True).exclude(email__in=[e.lower() for e in ldap_emails])
                deactivated = deactivated_qs.count()
                if deactivated > 0:
                    deactivated_qs.update(is_active=False)
                    self.stdout.write(f"  ⚠️  {deactivated} employé(s) désactivé(s) (supprimé(s) du LDAP)")
                
                # Désactiver aussi les utilisateurs Django qui ne sont plus dans LDAP
                # Récupérer les emails des employés LDAP actifs (uniquement ceux avec email)
                ldap_emails = set()
                for entry in results:
                    if hasattr(entry, 'mail') and entry.mail:
                        email_str = str(entry.mail).strip()
                        if email_str:  # Seulement si l'email n'est pas vide
                            ldap_emails.add(email_str.lower())
                    # Si l'email n'est pas dans mail, utiliser userPrincipalName ou générer depuis sAMAccountName
                    if not hasattr(entry, 'mail') or not entry.mail:
                        if hasattr(entry, 'userPrincipalName') and entry.userPrincipalName:
                            upn = str(entry.userPrincipalName).strip()
                            if upn and '@' in upn:
                                ldap_emails.add(upn.lower())
                        elif hasattr(entry, 'sAMAccountName') and entry.sAMAccountName:
                            sam = str(entry.sAMAccountName)
                            # Générer un email depuis sAMAccountName
                            generated_email = f"{sam}@sar.sn"
                            ldap_emails.add(generated_email.lower())
                
                # Désactiver les utilisateurs Django qui ne sont plus dans LDAP
                # (sauf les superusers et comptes admin locaux)
                # IMPORTANT: Seulement désactiver ceux qui ont un email (car sans email, ils ne peuvent pas se connecter de toute façon)
                deactivated_users_qs = User.objects.filter(
                    is_active=True,
                    email__isnull=False
                ).exclude(
                    email__in=ldap_emails
                ).exclude(
                    email=''  # Ne pas désactiver ceux sans email
                ).exclude(
                    is_superuser=True
                )
                deactivated_users_count = deactivated_users_qs.count()
                if deactivated_users_count > 0:
                    deactivated_users_qs.update(is_active=False)
                    self.stdout.write(f"  ⚠️  {deactivated_users_count} utilisateur(s) Django désactivé(s) (supprimé(s) du LDAP)")

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
