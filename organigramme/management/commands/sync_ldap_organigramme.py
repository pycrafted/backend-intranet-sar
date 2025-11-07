"""
Management command pour synchroniser l'organigramme depuis LDAP Active Directory
Usage: python manage.py sync_ldap_organigramme
"""
from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.core.files.base import ContentFile
from django.conf import settings
from organigramme.models import Direction, Agent
from decouple import config
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronise l\'organigramme depuis LDAP Active Directory (création, mise à jour, suppression des agents)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule sans modifier la base de données',
        )
        parser.add_argument(
            '--no-avatars',
            action='store_true',
            help='Ignore la synchronisation des avatars (thumbnailPhoto)',
        )

    def extract_department_from_dn(self, distinguished_name):
        """
        Extrait le département/direction depuis le DN (distinguishedName) en analysant les OU
        
        Args:
            distinguished_name: Le DN complet (ex: CN=Nom,OU=Utilisateurs,OU=Informatique,OU=UsersWifi,DC=sar,DC=sn)
            
        Returns:
            str: Le nom du département/direction ou None
        """
        if not distinguished_name:
            return None
        
        try:
            dn_parts = str(distinguished_name).split(',')
            generic_ous = ['Utilisateurs', 'UsersWifi', 'Users', 'Computers', 'Groups', 'Domain Controllers']
            ou_parts = []
            
            for part in dn_parts:
                part = part.strip()
                if part.startswith('OU='):
                    ou_name = part[3:].strip()  # Enlever "OU="
                    if ou_name not in generic_ous:
                        ou_parts.append(ou_name)
            
            # Prendre la première OU non générique (généralement le département/direction)
            if ou_parts:
                return ou_parts[0].strip()
            
            # Fallback: prendre la dernière OU non générique
            all_ous = [part[3:].strip() for part in dn_parts if part.strip().startswith('OU=')]
            if all_ous:
                for ou in reversed(all_ous):
                    if ou not in generic_ous:
                        return ou.strip()
            
            return None
        except Exception as e:
            logger.debug(f"Erreur extraction département depuis DN {distinguished_name}: {e}")
            return None
    
    def extract_all_ous_from_dn(self, distinguished_name):
        """
        Extrait toutes les OU non génériques depuis le DN
        
        Args:
            distinguished_name: Le DN complet
            
        Returns:
            list: Liste des noms de directions/départements
        """
        if not distinguished_name:
            return []
        
        try:
            dn_parts = str(distinguished_name).split(',')
            generic_ous = ['Utilisateurs', 'UsersWifi', 'Users', 'Computers', 'Groups', 'Domain Controllers']
            ou_parts = []
            
            for part in dn_parts:
                part = part.strip()
                if part.startswith('OU='):
                    ou_name = part[3:].strip()
                    if ou_name not in generic_ous:
                        ou_parts.append(ou_name.strip())
            
            return ou_parts
        except Exception as e:
            logger.debug(f"Erreur extraction toutes les OU depuis DN {distinguished_name}: {e}")
            return []
    
    def get_manager_from_ldap_dn(self, manager_dn, conn, ldap_base_dn, ldap_bind_dn, ldap_bind_password):
        """
        Trouve l'Agent correspondant au manager depuis son DN LDAP
        
        Args:
            manager_dn: Le DN du manager
            conn: Connexion LDAP existante
            ldap_base_dn: Base DN LDAP
            ldap_bind_dn: DN pour bind LDAP
            ldap_bind_password: Mot de passe pour bind LDAP
            
        Returns:
            Agent: L'agent correspondant au manager, ou None
        """
        if not manager_dn:
            return None
        
        try:
            # Méthode 1: Chercher le manager dans LDAP pour obtenir son email
            try:
                conn_mgr = Connection(conn.server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
                try:
                    conn_mgr.search(
                        search_base=str(manager_dn),
                        search_filter='(objectClass=user)',
                        search_scope=SUBTREE,
                        attributes=['mail', 'userPrincipalName']
                    )
                except Exception:
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
                            manager_agent = Agent.objects.get(email=manager_email)
                            conn_mgr.unbind()
                            return manager_agent
                        except Agent.DoesNotExist:
                            pass
                
                conn_mgr.unbind()
            except Exception as ldap_mgr_error:
                logger.debug(f"Erreur recherche LDAP manager {manager_dn}: {ldap_mgr_error}")
            
            # Méthode 2: Fallback - Chercher par le nom extrait du CN
            dn_parts = str(manager_dn).split(',')
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
                    manager_agent = Agent.objects.filter(
                        first_name__iexact=name_parts[0],
                        last_name__iexact=' '.join(name_parts[1:])
                    ).first()
                    if manager_agent:
                        return manager_agent
                    
                    # Essayer "Nom Prénom"
                    manager_agent = Agent.objects.filter(
                        first_name__iexact=' '.join(name_parts[:-1]),
                        last_name__iexact=name_parts[-1]
                    ).first()
                    if manager_agent:
                        return manager_agent
            
            return None
        except Exception as e:
            logger.debug(f"Erreur lors de la recherche du manager depuis DN {manager_dn}: {e}")
            return None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sync_avatars = not options['no_avatars']
        
        self.stdout.write("🔗 Début de la synchronisation LDAP pour l'organigramme...")
        
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
            conn = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True, auto_encode=False)
            self.stdout.write(self.style.SUCCESS(f"✅ Connexion LDAP réussie avec {ldap_bind_dn}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Échec connexion LDAP: {e}")
            )
            return

        # Filtre LDAP pour les utilisateurs actifs (exclut les comptes système)
        # Comptes supplémentaires à exclure pour l'organigramme :
        # assistantRH, COMPTABLE, star, IP21, ssarr, sapnotifications, adconnectsar,
        # SAPClusterSysAdmin, Netbackupservice, StagiaireCG, cdumont
        # On utilise un filtre spécifique pour l'organigramme avec les exclusions supplémentaires
        base_filter = getattr(settings, 'LDAP_USER_FILTER', 
            "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
            "(!(sAMAccountName=*$))(!(sAMAccountName=HealthMailbox*))(!(sAMAccountName=IUSR_*))"
            "(!(sAMAccountName=IWAM_*))(!(sAMAccountName=MSOL_*))(!(sAMAccountName=AAD_*))"
            "(!(sAMAccountName=ASPNET))(!(sAMAccountName=Administrateur))"
            "(!(sAMAccountName=docubase))(!(sAMAccountName=sc1adm))(!(sAMAccountName=SAPServiceSC1))"
            "(!(sAMAccountName=ISEADMIN))(!(sAMAccountName=user.test.01))(!(sAMAccountName=solarwinds))"
            "(!(sAMAccountName=SAC_FTP))(!(sAMAccountName=SQLSERVICE)))")
        
        # Ajouter les exclusions spécifiques pour l'organigramme
        # Retirer les parenthèses fermantes finales du filtre de base et ajouter les exclusions
        if base_filter.endswith('))'):
            base_filter = base_filter[:-2]  # Retirer '))' (ferme la dernière condition et le &)
        elif base_filter.endswith(')'):
            base_filter = base_filter[:-1]  # Retirer ')' (ferme le &)
        
        # Ajouter les exclusions supplémentaires pour l'organigramme
        # Le filtre doit se terminer par )) : une pour fermer la dernière condition, une pour fermer le &
        filterstr = (
            base_filter +
            "(!(sAMAccountName=assistantRH))(!(sAMAccountName=COMPTABLE))(!(sAMAccountName=star))"
            "(!(sAMAccountName=IP21))(!(sAMAccountName=ssarr))(!(sAMAccountName=sapnotifications))"
            "(!(sAMAccountName=adconnectsar))(!(sAMAccountName=SAPClusterSysAdmin))"
            "(!(sAMAccountName=Netbackupservice))(!(sAMAccountName=StagiaireCG))(!(sAMAccountName=cdumont))"
            "))"
        )
        
        # Attributs à récupérer
        attrs = [
            'givenName',           # Prénom
            'sn',                  # Nom de famille
            'mail',                # Email
            'ipPhone',             # Téléphone fixe
            'telephoneNumber',     # Téléphone mobile
            'title',               # Poste (job_title)
            'sAMAccountName',      # Nom d'utilisateur Windows (pour générer le matricule)
            'thumbnailPhoto',      # Photo de profil
            'displayName',         # Nom d'affichage
            'distinguishedName',   # DN complet pour extraire les directions (OU)
            'manager',             # Manager (N+1) - DN du manager
        ]

        try:
            self.stdout.write(f"🔍 Recherche des utilisateurs dans {ldap_base_dn}...")
            
            # Recherche LDAP
            conn.search(
                search_base=ldap_base_dn,
                search_filter=filterstr,
                search_scope=SUBTREE,
                attributes=attrs,
                get_operational_attributes=False
            )
            results = conn.entries
            # Garder une référence à conn.response pour accéder aux données binaires brutes
            ldap_responses = {}
            for response in conn.response:
                if 'dn' in response and 'attributes' in response:
                    ldap_responses[response['dn']] = response
            
            self.stdout.write(f"📊 {len(results)} entrées LDAP trouvées")
            
            created = 0
            updated = 0
            skipped = 0
            ldap_emails = set()
            
            with transaction.atomic():
                if dry_run:
                    # En mode dry-run, on ne fait pas de transaction
                    pass
                
                for entry in results:
                    try:
                        # Récupérer le sAMAccountName (obligatoire)
                        if not hasattr(entry, 'sAMAccountName') or not entry.sAMAccountName:
                            skipped += 1
                            continue
                        
                        sam = str(entry.sAMAccountName).strip()
                        
                        # Email (peut être vide si non renseigné dans LDAP)
                        email = None
                        if hasattr(entry, 'mail') and entry.mail:
                            email = str(entry.mail).strip()
                        elif hasattr(entry, 'userPrincipalName') and entry.userPrincipalName:
                            email = str(entry.userPrincipalName).strip()
                        
                        # Si pas d'email, laisser vide (l'utilisateur le renseignera plus tard dans LDAP)
                        if email:
                            email = email.lower()
                            ldap_emails.add(email)
                        else:
                            self.stdout.write(f"  ℹ️  {sam}: Pas d'email dans LDAP, champ email laissé vide")
                        
                        # Prénom = givenName
                        first_name = ''
                        if hasattr(entry, 'givenName') and entry.givenName:
                            first_name = str(entry.givenName).strip()
                        
                        # Nom = sn
                        last_name = ''
                        if hasattr(entry, 'sn') and entry.sn:
                            last_name = str(entry.sn).strip()
                        
                        # Si pas de prénom/nom, essayer displayName
                        if not first_name and not last_name:
                            if hasattr(entry, 'displayName') and entry.displayName:
                                display_name = str(entry.displayName).strip()
                                parts = display_name.split(' ', 1)
                                if len(parts) > 0:
                                    first_name = parts[0]
                                if len(parts) > 1:
                                    last_name = parts[1]
                        
                        # Fallback: utiliser sam si toujours pas de nom
                        if not first_name:
                            first_name = sam
                        if not last_name:
                            last_name = sam
                        
                        # Poste = title
                        job_title = ''
                        if hasattr(entry, 'title') and entry.title:
                            job_title = str(entry.title).strip()
                        if not job_title:
                            job_title = 'Non renseigné'
                        
                        # Téléphone fixe = ipPhone
                        phone_fixed = ''
                        if hasattr(entry, 'ipPhone') and entry.ipPhone:
                            phone_fixed = str(entry.ipPhone).strip()
                        
                        # Téléphone mobile = telephoneNumber
                        phone_mobile = ''
                        if hasattr(entry, 'telephoneNumber') and entry.telephoneNumber:
                            phone_mobile = str(entry.telephoneNumber).strip()
                        
                        # Matricule: générer depuis sAMAccountName (car n'existe pas dans LDAP)
                        # Utiliser sAMAccountName comme matricule unique (en majuscules)
                        matricule = sam.upper()
                        
                        # Direction principale - Extraire depuis distinguishedName (OU)
                        main_direction_name = None
                        if hasattr(entry, 'distinguishedName') and entry.distinguishedName:
                            main_direction_name = self.extract_department_from_dn(str(entry.distinguishedName))
                        
                        # Créer la direction principale si elle n'existe pas
                        main_direction = None
                        if main_direction_name:
                            main_direction, _ = Direction.objects.get_or_create(
                                name=main_direction_name,
                                defaults={'name': main_direction_name}
                            )
                        
                        # Toutes les directions - Extraire toutes les OU non génériques
                        all_direction_names = []
                        if hasattr(entry, 'distinguishedName') and entry.distinguishedName:
                            all_direction_names = self.extract_all_ous_from_dn(str(entry.distinguishedName))
                        
                        # Créer toutes les directions si elles n'existent pas
                        directions_list = []
                        for dir_name in all_direction_names:
                            direction, _ = Direction.objects.get_or_create(
                                name=dir_name,
                                defaults={'name': dir_name}
                            )
                            directions_list.append(direction)
                        
                        # Manager (N+1) - Extraire depuis le champ manager (DN)
                        manager_agent = None
                        if hasattr(entry, 'manager') and entry.manager:
                            manager_dn = str(entry.manager)
                            manager_agent = self.get_manager_from_ldap_dn(
                                manager_dn, conn, ldap_base_dn, ldap_bind_dn, ldap_bind_password
                            )
                        
                        # Chercher l'agent existant
                        agent = None
                        if email:
                            # Priorité 1: Chercher par email si disponible
                            try:
                                agent = Agent.objects.get(email=email)
                            except Agent.DoesNotExist:
                                pass
                            except Agent.MultipleObjectsReturned:
                                # Si plusieurs agents avec le même email, prendre le premier
                                agent = Agent.objects.filter(email=email).first()
                        
                        # Priorité 2: Si pas trouvé par email, chercher par matricule
                        if not agent:
                            try:
                                agent = Agent.objects.get(matricule=matricule)
                                # Si trouvé par matricule mais email différent, mettre à jour l'email
                                if email and agent.email != email:
                                    if not dry_run:
                                        agent.email = email
                                        agent.save(update_fields=['email'])
                                    self.stdout.write(f"  🔄 Email mis à jour pour matricule {matricule}")
                            except Agent.DoesNotExist:
                                pass
                        
                        # Si le matricule existe déjà pour un autre agent, générer un matricule unique
                        if agent and agent.matricule != matricule:
                            # L'agent existe mais avec un autre matricule, on garde le matricule LDAP
                            # (sAMAccountName est unique dans LDAP)
                            existing_agent_with_matricule = None
                            try:
                                existing_agent_with_matricule = Agent.objects.get(matricule=matricule)
                                if existing_agent_with_matricule.id != agent.id:
                                    # Conflit: un autre agent a déjà ce matricule
                                    # Générer un matricule unique en ajoutant un suffixe
                                    base_matricule = matricule
                                    counter = 1
                                    while Agent.objects.filter(matricule=matricule).exclude(id=agent.id).exists():
                                        matricule = f"{base_matricule}_{counter}"
                                        counter += 1
                                    self.stdout.write(f"  ⚠️  Matricule modifié pour {email}: {base_matricule} → {matricule}")
                            except Agent.DoesNotExist:
                                pass
                        elif not agent:
                            # Vérifier si le matricule existe déjà
                            if Agent.objects.filter(matricule=matricule).exists():
                                # Générer un matricule unique
                                base_matricule = matricule
                                counter = 1
                                while Agent.objects.filter(matricule=matricule).exists():
                                    matricule = f"{base_matricule}_{counter}"
                                    counter += 1
                                self.stdout.write(f"  ⚠️  Matricule modifié pour {email}: {base_matricule} → {matricule}")
                        
                        agent_created = False
                        if not agent:
                            # Créer un nouvel agent
                            if not dry_run:
                                agent = Agent.objects.create(
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email or None,  # Email peut être None
                                    job_title=job_title,
                                    phone_fixed=phone_fixed or None,
                                    phone_mobile=phone_mobile or None,
                                    matricule=matricule,
                                    main_direction=main_direction,
                                    manager=manager_agent,
                                )
                                # Ajouter toutes les directions
                                if directions_list:
                                    agent.directions.set(directions_list)
                                agent_created = True
                            else:
                                email_display = email or "(pas d'email)"
                                self.stdout.write(f"  [DRY-RUN] Créerait: {first_name} {last_name} ({email_display})")
                                created += 1
                                continue
                        else:
                            # Mettre à jour l'agent existant
                            updated_fields = []
                            if agent.first_name != first_name:
                                agent.first_name = first_name
                                updated_fields.append('first_name')
                            if agent.last_name != last_name:
                                agent.last_name = last_name
                                updated_fields.append('last_name')
                            if agent.job_title != job_title:
                                agent.job_title = job_title
                                updated_fields.append('job_title')
                            if agent.phone_fixed != phone_fixed:
                                agent.phone_fixed = phone_fixed or None
                                updated_fields.append('phone_fixed')
                            if agent.phone_mobile != phone_mobile:
                                agent.phone_mobile = phone_mobile or None
                                updated_fields.append('phone_mobile')
                            # Mettre à jour l'email seulement s'il existe dans LDAP
                            if email and agent.email != email:
                                agent.email = email
                                updated_fields.append('email')
                            elif not email and agent.email:
                                # Si l'email n'existe plus dans LDAP, le vider
                                agent.email = None
                                updated_fields.append('email')
                            if agent.main_direction != main_direction:
                                agent.main_direction = main_direction
                                updated_fields.append('main_direction')
                            if agent.manager != manager_agent:
                                agent.manager = manager_agent
                                updated_fields.append('manager')
                            
                            # Mettre à jour les directions
                            if directions_list:
                                current_directions = set(agent.directions.all())
                                new_directions = set(directions_list)
                                if current_directions != new_directions:
                                    agent.directions.set(directions_list)
                                    updated_fields.append('directions')
                            
                            # Mettre à jour le matricule si différent
                            if agent.matricule != matricule:
                                agent.matricule = matricule
                                updated_fields.append('matricule')
                            
                            if updated_fields and not dry_run:
                                agent.save(update_fields=updated_fields)
                            elif dry_run and updated_fields:
                                self.stdout.write(f"  [DRY-RUN] Mettrait à jour: {first_name} {last_name} ({email})")
                        
                        # Synchroniser l'avatar (thumbnailPhoto)
                        if sync_avatars and not dry_run:
                            try:
                                entry_dn = None
                                if hasattr(entry, 'distinguishedName') and entry.distinguishedName:
                                    entry_dn = str(entry.distinguishedName)
                                
                                if entry_dn and entry_dn in ldap_responses:
                                    response_data = ldap_responses[entry_dn]
                                    raw_attributes = response_data.get('raw_attributes', {})
                                    
                                    photo_data = None
                                    if 'thumbnailPhoto' in raw_attributes:
                                        photo_raw = raw_attributes['thumbnailPhoto']
                                        if isinstance(photo_raw, list) and len(photo_raw) > 0:
                                            photo_data = photo_raw[0]
                                        elif isinstance(photo_raw, bytes):
                                            photo_data = photo_raw
                                    
                                    # Si pas trouvé dans raw_attributes, faire une recherche individuelle
                                    if not photo_data:
                                        try:
                                            conn_photo = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True, auto_encode=False)
                                            conn_photo.search(
                                                search_base=entry_dn,
                                                search_filter='(objectClass=user)',
                                                search_scope=SUBTREE,
                                                attributes=['thumbnailPhoto']
                                            )
                                            
                                            if conn_photo.response:
                                                for resp in conn_photo.response:
                                                    if 'raw_attributes' in resp and 'thumbnailPhoto' in resp['raw_attributes']:
                                                        photo_raw = resp['raw_attributes']['thumbnailPhoto']
                                                        if isinstance(photo_raw, list) and len(photo_raw) > 0:
                                                            photo_data = photo_raw[0]
                                                        elif isinstance(photo_raw, bytes):
                                                            photo_data = photo_raw
                                                        break
                                            
                                            conn_photo.unbind()
                                        except Exception as photo_error:
                                            logger.debug(f"Erreur recherche photo individuelle pour {sam}: {photo_error}")
                                    
                                    if photo_data and len(photo_data) > 100:
                                        # Vérifier que c'est bien une image
                                        is_valid_image = (
                                            (len(photo_data) >= 2 and photo_data[:2] == b'\xff\xd8') or  # JPEG
                                            (len(photo_data) >= 8 and photo_data[:8] == b'\x89PNG\r\n\x1a\n') or  # PNG
                                            (len(photo_data) >= 4 and photo_data[:4] == b'GIF8')  # GIF
                                        )
                                        
                                        if is_valid_image:
                                            agent.avatar.save(
                                                f"avatars/{sam}.jpg",
                                                ContentFile(photo_data),
                                                save=True
                                            )
                                            logger.debug(f"Avatar synchronisé pour {sam}")
                            except Exception as avatar_error:
                                logger.error(f"Erreur synchronisation avatar pour {sam}: {avatar_error}")
                        
                        if agent_created:
                            created += 1
                            self.stdout.write(f"  ✅ Créé: {first_name} {last_name} ({email})")
                        else:
                            updated += 1
                            if not dry_run:
                                self.stdout.write(f"  🔄 Mis à jour: {first_name} {last_name} ({email})")
                    
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement de l'entrée LDAP: {e}", exc_info=True)
                        skipped += 1
                        self.stdout.write(f"  ⚠️  Erreur: {str(e)}")
                
                # Supprimer les agents qui ne sont plus dans LDAP
                # Note: On ne supprime que ceux qui ont un email ET qui ne sont plus dans LDAP
                # Les agents sans email ne sont pas supprimés car ils peuvent être en cours de création
                if not dry_run:
                    # Récupérer tous les matricules des entrées LDAP pour vérifier aussi par matricule
                    ldap_matricules = set()
                    for entry in results:
                        if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName:
                            sam = str(entry.sAMAccountName).strip().upper()
                            ldap_matricules.add(sam)
                    
                    # Supprimer les agents qui ne sont plus dans LDAP (vérifier par email OU matricule)
                    agents_to_delete = Agent.objects.exclude(
                        models.Q(email__in=[e.lower() for e in ldap_emails]) | 
                        models.Q(matricule__in=ldap_matricules)
                    )
                    deleted_count = agents_to_delete.count()
                    if deleted_count > 0:
                        agents_to_delete.delete()
                        self.stdout.write(f"  🗑️  {deleted_count} agent(s) supprimé(s) (plus dans LDAP)")
            
            if dry_run:
                # Annuler la transaction en mode dry-run
                transaction.rollback()
            
            conn.unbind()

            # Résumé
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS(f"Synchronisation terminée : {created} créés, {updated} mis à jour, {skipped} ignorés"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
            # Reconstruire la hiérarchie
            if not dry_run:
                self.stdout.write("\n🔄 Reconstruction de la hiérarchie...")
                Agent.rebuild_hierarchy_levels()
                self.stdout.write(self.style.SUCCESS("✅ Hiérarchie reconstruite"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de la synchronisation: {e}")
            )
            import traceback
            logger.error(traceback.format_exc())
            conn.unbind()

