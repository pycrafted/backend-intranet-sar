"""
Backend d'authentification LDAP personnalisé pour la SAR
Permet aux utilisateurs de se connecter avec leur email et mot de passe LDAP
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from ldap3 import Server, Connection, ALL, SUBTREE
from decouple import config
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class LDAPBackend(BaseBackend):
    """
    Backend d'authentification LDAP personnalisé
    Authentifie les utilisateurs contre Active Directory LDAP de la SAR
    LDAP est optionnel : si le serveur n'est pas accessible, le backend retourne None
    et Django utilisera le ModelBackend pour l'authentification locale
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie un utilisateur contre LDAP
        
        Args:
            request: La requête HTTP
            username: Email ou sAMAccountName de l'utilisateur
            password: Mot de passe de l'utilisateur
            
        Returns:
            User: L'utilisateur Django authentifié, ou None si l'authentification échoue
            None est retourné silencieusement si LDAP n'est pas disponible pour permettre
            au ModelBackend de prendre le relais
        """
        if not username or not password:
            return None
        
        # Vérifier si LDAP est activé (optionnel via variable d'environnement)
        ldap_enabled = config('LDAP_ENABLED', default='True', cast=bool)
        if not ldap_enabled:
            logger.debug("ℹ️ [LDAP_AUTH] LDAP désactivé (LDAP_ENABLED=False), passage au backend suivant")
            return None
        
        # Récupérer les paramètres LDAP depuis settings
        # Si les paramètres ne sont pas configurés, retourner None silencieusement
        try:
            ldap_server = getattr(settings, 'LDAP_SERVER', config('LDAP_SERVER', default=''))
            ldap_port = getattr(settings, 'LDAP_PORT', config('LDAP_PORT', default=389, cast=int))
            ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', config('LDAP_BASE_DN', default='DC=sar,DC=sn'))
        except Exception as config_error:
            logger.debug(f"ℹ️ [LDAP_AUTH] Configuration LDAP manquante ou invalide: {config_error}, passage au backend suivant")
            return None
        
        # Si le serveur LDAP n'est pas configuré, retourner None silencieusement
        if not ldap_server:
            logger.debug("ℹ️ [LDAP_AUTH] LDAP_SERVER non configuré, passage au backend suivant")
            return None
        
        # Normaliser le username (email ou sAMAccountName)
        # Si c'est un email, extraire le sAMAccountName (partie avant @)
        if '@' in username:
            email = username
            sam_account_name = email.split('@')[0]
        else:
            sam_account_name = username
            email = None
        
        logger.info(f"🔐 [LDAP_AUTH] Tentative d'authentification pour: {sam_account_name}")
        
        try:
            # Connexion au serveur LDAP avec timeout pour éviter les blocages
            # Si le serveur n'est pas accessible, on retourne None silencieusement
            try:
                server = Server(ldap_server, port=ldap_port, get_info=ALL, connect_timeout=5)
            except Exception as server_error:
                logger.debug(f"ℹ️ [LDAP_AUTH] Serveur LDAP non accessible ({ldap_server}:{ldap_port}): {server_error}, passage au backend suivant")
                return None
            
            # Essayer de se connecter avec les credentials de l'utilisateur
            # Format du DN: CN=Nom Complet,OU=...,DC=sar,DC=sn
            # On va d'abord chercher l'utilisateur pour obtenir son DN
            bind_dn = getattr(settings, 'LDAP_BIND_DN', config('LDAP_BIND_DN', default=''))
            bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', config('LDAP_BIND_PASSWORD', default=''))
            
            if not bind_dn or not bind_password:
                logger.debug("ℹ️ [LDAP_AUTH] LDAP_BIND_DN ou LDAP_BIND_PASSWORD non configuré, passage au backend suivant")
                return None
            
            # Connexion avec le compte de service pour rechercher l'utilisateur
            # Si la connexion échoue (timeout, serveur inaccessible, etc.), retourner None silencieusement
            try:
                conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True, receive_timeout=5)
            except Exception as bind_error:
                # Erreur de connexion (timeout, serveur inaccessible, etc.)
                # Retourner None silencieusement pour permettre au ModelBackend de prendre le relais
                logger.debug(f"ℹ️ [LDAP_AUTH] Connexion LDAP impossible ({ldap_server}:{ldap_port}): {bind_error}, passage au backend suivant")
                return None
            
            # Rechercher l'utilisateur par sAMAccountName ou email
            search_filter = f"(&(objectClass=user)(objectCategory=person)(sAMAccountName={sam_account_name}))"
            if email:
                # Si on a un email, essayer aussi avec mail
                search_filter = f"(&(objectClass=user)(objectCategory=person)(|(sAMAccountName={sam_account_name})(mail={email})))"
            
            try:
                conn.search(
                    search_base=ldap_base_dn,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=[
                        'sAMAccountName', 'mail', 'givenName', 'sn', 'displayName', 'userPrincipalName', 
                        'distinguishedName', 'title', 'ipPhone', 'telephoneNumber', 'manager'
                    ],
                    time_limit=5  # Timeout de 5 secondes pour la recherche
                )
            except Exception as search_error:
                # Erreur de recherche LDAP - retourner None silencieusement
                logger.debug(f"ℹ️ [LDAP_AUTH] Erreur recherche LDAP: {search_error}, passage au backend suivant")
                try:
                    conn.unbind()
                except:
                    pass
                return None
            
            if not conn.entries:
                # Utilisateur non trouvé dans LDAP - retourner None pour permettre au ModelBackend de prendre le relais
                logger.debug(f"ℹ️ [LDAP_AUTH] Utilisateur {sam_account_name} non trouvé dans LDAP, passage au backend suivant")
                try:
                    conn.unbind()
                except:
                    pass
                return None
            
            # Récupérer l'entrée LDAP
            ldap_entry = conn.entries[0]
            user_dn = None
            if hasattr(ldap_entry, 'entry_dn'):
                user_dn = str(ldap_entry.entry_dn)
            elif hasattr(ldap_entry, 'dn'):
                user_dn = str(ldap_entry.dn)
            elif hasattr(ldap_entry, 'distinguishedName'):
                user_dn = str(ldap_entry.distinguishedName)
            
            if not user_dn:
                logger.debug(f"ℹ️ [LDAP_AUTH] Impossible de récupérer le DN pour {sam_account_name}, passage au backend suivant")
                try:
                    conn.unbind()
                except:
                    pass
                return None
            
            ldap_email = str(ldap_entry.mail) if hasattr(ldap_entry, 'mail') and ldap_entry.mail else None
            ldap_sam = str(ldap_entry.sAMAccountName) if hasattr(ldap_entry, 'sAMAccountName') and ldap_entry.sAMAccountName else sam_account_name
            
            # Si on cherchait par email mais qu'on a trouvé par sAMAccountName, utiliser l'email LDAP
            if email and ldap_email:
                email = ldap_email
            
            try:
                conn.unbind()
            except:
                pass
            
            # Maintenant, essayer de s'authentifier avec les credentials de l'utilisateur
            # Essayer d'abord avec userPrincipalName (format email), puis avec le DN
            auth_success = False
            try:
                # Méthode 1: Authentifier avec userPrincipalName (format: email@sar.sn)
                user_principal_name = str(ldap_entry.userPrincipalName) if hasattr(ldap_entry, 'userPrincipalName') and ldap_entry.userPrincipalName else None
                if user_principal_name:
                    try:
                        user_conn = Connection(server, user=user_principal_name, password=password, auto_bind=True, receive_timeout=5)
                        auth_success = True
                        logger.info(f"✅ [LDAP_AUTH] Authentification LDAP réussie avec userPrincipalName pour {ldap_sam}")
                        try:
                            user_conn.unbind()
                        except:
                            pass
                    except Exception:
                        pass
                
                # Méthode 2: Si la méthode 1 échoue, essayer avec le DN
                if not auth_success:
                    try:
                        user_conn = Connection(server, user=user_dn, password=password, auto_bind=True, receive_timeout=5)
                        auth_success = True
                        logger.info(f"✅ [LDAP_AUTH] Authentification LDAP réussie avec DN pour {ldap_sam}")
                        try:
                            user_conn.unbind()
                        except:
                            pass
                    except Exception as dn_auth_error:
                        pass
                
                # Méthode 3: Essayer avec sAMAccountName@sar.sn (format UPN)
                if not auth_success:
                    try:
                        upn_format = f"{ldap_sam}@sar.sn"
                        user_conn = Connection(server, user=upn_format, password=password, auto_bind=True, receive_timeout=5)
                        auth_success = True
                        logger.info(f"✅ [LDAP_AUTH] Authentification LDAP réussie avec UPN format pour {ldap_sam}")
                        try:
                            user_conn.unbind()
                        except:
                            pass
                    except Exception:
                        pass
                
                if not auth_success:
                    # Authentification LDAP échouée - retourner None pour permettre au ModelBackend de prendre le relais
                    logger.debug(f"ℹ️ [LDAP_AUTH] Authentification LDAP échouée pour {ldap_sam}, passage au backend suivant")
                    return None
                    
            except Exception as auth_error:
                # Erreur lors de l'authentification - retourner None silencieusement
                logger.debug(f"ℹ️ [LDAP_AUTH] Erreur lors de l'authentification LDAP pour {ldap_sam}: {auth_error}, passage au backend suivant")
                return None
            
            # Récupérer ou créer l'utilisateur Django
            user = self.get_or_create_user(ldap_sam, email or ldap_email, ldap_entry)
            
            return user
            
        except Exception as e:
            # Erreur générale LDAP (timeout, serveur inaccessible, etc.)
            # Retourner None silencieusement pour permettre au ModelBackend de prendre le relais
            logger.debug(f"ℹ️ [LDAP_AUTH] Erreur LDAP pour {sam_account_name}: {e}, passage au backend suivant")
            return None
    
    def extract_department_from_dn(self, distinguished_name):
        """
        Extrait le département depuis le DN (distinguishedName) en analysant les OU
        
        Args:
            distinguished_name: Le DN complet (ex: CN=Nom,OU=Utilisateurs,OU=Informatique,OU=UsersWifi,DC=sar,DC=sn)
            
        Returns:
            str: Le nom du département ou None
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
            
            # Prendre la première OU non générique (généralement le département)
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
    
    def get_manager_from_ldap_dn(self, manager_dn):
        """
        Trouve le User Django correspondant au manager depuis son DN LDAP
        Recherche d'abord dans LDAP pour obtenir l'email du manager, puis trouve le User Django
        
        Args:
            manager_dn: Le DN du manager (ex: CN=Manager Name,OU=...,DC=sar,DC=sn)
            
        Returns:
            User: L'utilisateur Django correspondant au manager, ou None
        """
        if not manager_dn:
            return None
        
        try:
            # Méthode 1: Chercher le manager dans LDAP pour obtenir son email
            # Puis chercher le User Django par email
            ldap_server = getattr(settings, 'LDAP_SERVER', config('LDAP_SERVER', default='10.113.243.2'))
            ldap_port = getattr(settings, 'LDAP_PORT', config('LDAP_PORT', default=389, cast=int))
            ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', config('LDAP_BASE_DN', default='DC=sar,DC=sn'))
            ldap_bind_dn = getattr(settings, 'LDAP_BIND_DN', config('LDAP_BIND_DN', default=''))
            ldap_bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', config('LDAP_BIND_PASSWORD', default=''))
            
            if ldap_bind_dn and ldap_bind_password:
                try:
                    server = Server(ldap_server, port=ldap_port, get_info=ALL)
                    conn = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
                    
                    # Rechercher le manager par son DN exact
                    # Utiliser le DN comme search_base et un filtre simple
                    try:
                        conn.search(
                            search_base=str(manager_dn),
                            search_filter='(objectClass=user)',
                            search_scope=SUBTREE,
                            attributes=['mail', 'sAMAccountName', 'userPrincipalName']
                        )
                    except Exception:
                        # Si la recherche par DN direct échoue, chercher dans toute la base
                        conn.search(
                            search_base=ldap_base_dn,
                            search_filter=f'(&(objectClass=user)(distinguishedName={manager_dn}))',
                            search_scope=SUBTREE,
                            attributes=['mail', 'sAMAccountName', 'userPrincipalName']
                        )
                    
                    if conn.entries:
                        manager_entry = conn.entries[0]
                        # Essayer d'obtenir l'email du manager
                        manager_email = None
                        if hasattr(manager_entry, 'mail') and manager_entry.mail:
                            manager_email = str(manager_entry.mail).strip()
                        elif hasattr(manager_entry, 'userPrincipalName') and manager_entry.userPrincipalName:
                            manager_email = str(manager_entry.userPrincipalName).strip()
                        
                        if manager_email:
                            try:
                                manager = User.objects.get(email=manager_email)
                                conn.unbind()
                                return manager
                            except User.DoesNotExist:
                                pass
                    
                    conn.unbind()
                except Exception as ldap_error:
                    logger.debug(f"Erreur lors de la recherche LDAP du manager {manager_dn}: {ldap_error}")
            
            # Méthode 2: Fallback - Chercher par le nom extrait du CN
            # Extraire le CN du DN pour obtenir le nom du manager
            # Format: CN=Nom Complet,OU=...
            dn_parts = str(manager_dn).split(',')
            cn_part = None
            for part in dn_parts:
                part = part.strip()
                if part.startswith('CN='):
                    cn_part = part[3:].strip()  # Enlever "CN="
                    break
            
            if not cn_part:
                return None
            
            # Essayer de trouver le manager par son nom complet
            # Le nom dans LDAP est généralement "Prénom Nom" ou "Nom Prénom"
            name_parts = cn_part.split()
            if len(name_parts) >= 2:
                # Essayer "Prénom Nom"
                manager = User.objects.filter(
                    first_name__iexact=name_parts[0],
                    last_name__iexact=' '.join(name_parts[1:])
                ).first()
                if manager:
                    return manager
                
                # Essayer "Nom Prénom" (si le format est inversé)
                manager = User.objects.filter(
                    first_name__iexact=' '.join(name_parts[:-1]),
                    last_name__iexact=name_parts[-1]
                ).first()
                if manager:
                    return manager
                
                # Essayer avec le nom complet dans first_name ou last_name
                manager = User.objects.filter(
                    first_name__icontains=cn_part
                ).first()
                if manager:
                    return manager
                
                manager = User.objects.filter(
                    last_name__icontains=cn_part
                ).first()
                if manager:
                    return manager
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur lors de la recherche du manager depuis DN {manager_dn}: {e}")
            return None
    
    def get_or_create_user(self, sam_account_name, email, ldap_entry):
        """
        Récupère ou crée un utilisateur Django depuis les données LDAP
        
        Args:
            sam_account_name: sAMAccountName de l'utilisateur
            email: Email de l'utilisateur
            ldap_entry: L'entrée LDAP de l'utilisateur
            
        Returns:
            User: L'utilisateur Django
        """
        try:
            # Essayer de trouver l'utilisateur par email uniquement
            # Le matricule n'existe pas dans LDAP et ne doit pas être utilisé pour la recherche
            user = None
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
            
            # Extraire toutes les données LDAP
            first_name = str(ldap_entry.givenName) if hasattr(ldap_entry, 'givenName') and ldap_entry.givenName else ''
            last_name = str(ldap_entry.sn) if hasattr(ldap_entry, 'sn') and ldap_entry.sn else ''
            display_name = str(ldap_entry.displayName) if hasattr(ldap_entry, 'displayName') and ldap_entry.displayName else ''
            
            # Si pas de prénom/nom, essayer displayName
            if not first_name and not last_name and display_name:
                parts = display_name.split(' ', 1)
                if len(parts) > 0:
                    first_name = parts[0]
                if len(parts) > 1:
                    last_name = parts[1]
            
            # Poste occupé (position) = title dans LDAP
            position = ''
            if hasattr(ldap_entry, 'title') and ldap_entry.title:
                position = str(ldap_entry.title).strip()
            
            # Téléphone fixe = ipPhone dans LDAP
            phone_fixed = ''
            if hasattr(ldap_entry, 'ipPhone') and ldap_entry.ipPhone:
                phone_fixed = str(ldap_entry.ipPhone).strip()
            
            # Téléphone personnel = telephoneNumber dans LDAP
            phone_number = ''
            if hasattr(ldap_entry, 'telephoneNumber') and ldap_entry.telephoneNumber:
                phone_number = str(ldap_entry.telephoneNumber).strip()
            
            # Département - Extraire depuis distinguishedName (OU)
            department = None
            department_name = None
            if hasattr(ldap_entry, 'distinguishedName') and ldap_entry.distinguishedName:
                department_name = self.extract_department_from_dn(str(ldap_entry.distinguishedName))
            
            if department_name:
                try:
                    from annuaire.models import Department
                    department, _ = Department.objects.get_or_create(
                        name=department_name,
                        defaults={'name': department_name}
                    )
                except Exception as dept_error:
                    logger.debug(f"Erreur lors de la création/récupération du département {department_name}: {dept_error}")
            
            # Manager (N+1) - Extraire depuis le champ manager (DN)
            manager = None
            if hasattr(ldap_entry, 'manager') and ldap_entry.manager:
                manager_dn = str(ldap_entry.manager)
                manager = self.get_manager_from_ldap_dn(manager_dn)
                if manager:
                    logger.debug(f"Manager trouvé pour {email}: {manager.email}")
                else:
                    logger.debug(f"Manager non trouvé pour {email} depuis DN {manager_dn}")
            
            if not user:
                # Créer un nouvel utilisateur
                # Générer un username unique (email sans @ ou sam_account_name)
                username = email.split('@')[0] if email and '@' in email else sam_account_name
                # S'assurer que le username est unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Créer l'utilisateur (sans mot de passe, car on utilise LDAP)
                # TOUJOURS actif pour les comptes LDAP avec email
                # Le champ matricule n'est PAS rempli car il n'existe pas dans LDAP
                # Il peut être renseigné manuellement dans l'admin Django
                user = User.objects.create_user(
                    username=username,
                    email=email or f"{sam_account_name}@sar.sn",
                    first_name=first_name or sam_account_name,
                    last_name=last_name or sam_account_name,
                    position=position or None,
                    phone_fixed=phone_fixed or None,
                    phone_number=phone_number or None,
                    department=department,
                    manager=manager,
                    # matricule non rempli - doit être renseigné manuellement si nécessaire
                    is_active=True  # TOUJOURS actif pour les comptes LDAP
                )
                
                # Définir un mot de passe hashé aléatoire (ne sera jamais utilisé car on utilise LDAP)
                # Mais nécessaire pour que Django accepte l'utilisateur
                user.set_unusable_password()
                user.save()
                
                logger.info(f"✅ [LDAP_AUTH] Utilisateur Django créé: {user.email} (username: {user.username})")
            else:
                # Mettre à jour les informations si nécessaire
                updated = False
                was_inactive = not user.is_active
                
                # Mettre à jour les champs de base
                if user.first_name != first_name and first_name:
                    user.first_name = first_name
                    updated = True
                if user.last_name != last_name and last_name:
                    user.last_name = last_name
                    updated = True
                if user.email != email and email:
                    user.email = email
                    updated = True
                
                # Poste occupé (position) = title dans LDAP
                if user.position != position and position:
                    user.position = position
                    updated = True
                
                # Téléphone fixe = ipPhone dans LDAP
                if user.phone_fixed != phone_fixed and phone_fixed:
                    user.phone_fixed = phone_fixed
                    updated = True
                
                # Téléphone personnel = telephoneNumber dans LDAP
                if user.phone_number != phone_number and phone_number:
                    user.phone_number = phone_number
                    updated = True
                
                # Département - Extraire depuis distinguishedName (OU)
                if department and user.department != department:
                    user.department = department
                    updated = True
                
                # Manager (N+1) - Mettre à jour si différent
                if manager and user.manager != manager:
                    user.manager = manager
                    updated = True
                elif not manager and user.manager:
                    # Si le manager n'est plus dans LDAP, le vider
                    user.manager = None
                    updated = True
                
                # Le matricule n'est PAS mis à jour automatiquement car il n'existe pas dans LDAP
                # Il doit être renseigné manuellement dans l'admin Django si nécessaire
                
                # IMPORTANT: TOUJOURS activer les comptes LDAP avec email
                # Même si aucun autre champ n'a changé, on doit s'assurer que l'utilisateur est actif
                if not user.is_active:
                    user.is_active = True
                    updated = True
                    logger.info(f"🔄 [LDAP_AUTH] Utilisateur Django réactivé: {user.email}")
                
                # Sauvegarder si des modifications ont été apportées
                if updated:
                    user.save()
                    if was_inactive:
                        logger.info(f"🔄 [LDAP_AUTH] Utilisateur Django réactivé et mis à jour: {user.email}")
                    else:
                        logger.info(f"🔄 [LDAP_AUTH] Utilisateur Django mis à jour: {user.email}")
                # Si aucun autre champ n'a changé mais que l'utilisateur était inactif, il a déjà été activé ci-dessus
            
            return user
            
        except Exception as e:
            logger.error(f"❌ [LDAP_AUTH] Erreur lors de la création/récupération de l'utilisateur: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_user(self, user_id):
        """
        Récupère un utilisateur par son ID
        Nécessaire pour que Django reconnaisse ce backend
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

