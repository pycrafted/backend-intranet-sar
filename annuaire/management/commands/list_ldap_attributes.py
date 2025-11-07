"""
Management command pour lister tous les attributs LDAP disponibles pour les utilisateurs
Usage: python manage.py list_ldap_attributes
"""
from ldap3 import Server, Connection, ALL, SUBTREE
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config
import json

class Command(BaseCommand):
    help = 'Liste tous les attributs LDAP disponibles pour les utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-user',
            type=str,
            help='sAMAccountName d\'un utilisateur spécifique à analyser',
        )
        parser.add_argument(
            '--all-attributes',
            action='store_true',
            help='Récupère tous les attributs (peut être très long)',
        )

    def handle(self, *args, **options):
        sample_user = options.get('sample_user')
        all_attributes = options.get('all_attributes')
        
        self.stdout.write("🔗 Connexion au LDAP pour lister les attributs disponibles...")
        
        # Configuration LDAP
        ldap_server = getattr(settings, 'LDAP_SERVER', config('LDAP_SERVER', default='10.113.243.2'))
        ldap_port = getattr(settings, 'LDAP_PORT', config('LDAP_PORT', default=389, cast=int))
        ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', config('LDAP_BASE_DN', default='DC=sar,DC=sn'))
        ldap_bind_dn = getattr(settings, 'LDAP_BIND_DN', config('LDAP_BIND_DN', default=''))
        ldap_bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', config('LDAP_BIND_PASSWORD', default=''))
        
        if not ldap_bind_password:
            self.stdout.write(
                self.style.ERROR("❌ LDAP_BIND_PASSWORD non configuré dans .env")
            )
            return
        
        try:
            # Connexion au serveur LDAP
            server = Server(ldap_server, port=ldap_port, get_info=ALL)
            conn = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Connexion LDAP réussie avec {ldap_bind_dn}"))
            
            # Filtre LDAP pour les utilisateurs actifs
            filterstr = getattr(settings, 'LDAP_USER_FILTER', 
                "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))")
            
            # Si un utilisateur spécifique est demandé, rechercher uniquement celui-ci
            if sample_user:
                filterstr = f"(&(objectClass=user)(objectCategory=person)(sAMAccountName={sample_user}))"
                self.stdout.write(f"🔍 Recherche de l'utilisateur spécifique: {sample_user}")
            else:
                self.stdout.write(f"🔍 Recherche des utilisateurs actifs...")
            
            # Récupérer tous les attributs disponibles
            if all_attributes:
                # Récupérer TOUS les attributs (peut être très long)
                attrs = ['*', '+']
                self.stdout.write(self.style.WARNING("⚠️  Mode 'tous les attributs' - cela peut prendre du temps..."))
            else:
                # Récupérer les attributs standard + opérationnels
                attrs = ['*', '+', 'memberOf', 'proxyAddresses', 'userAccountControl']
            
            # Recherche LDAP
            conn.search(
                search_base=ldap_base_dn,
                search_filter=filterstr,
                search_scope=SUBTREE,
                attributes=attrs if all_attributes else ['*', '+'],
                size_limit=10 if sample_user else 5  # Limiter à 5 utilisateurs pour l'analyse
            )
            
            if not conn.entries:
                self.stdout.write(self.style.ERROR("❌ Aucun utilisateur trouvé"))
                conn.unbind()
                return
            
            self.stdout.write(f"\n✅ {len(conn.entries)} utilisateur(s) trouvé(s)\n")
            self.stdout.write("=" * 80)
            
            # Analyser chaque utilisateur trouvé
            for idx, entry in enumerate(conn.entries, 1):
                sam = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else "UNKNOWN"
                display_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else "N/A"
                
                self.stdout.write(f"\n{'=' * 80}")
                self.stdout.write(f"👤 UTILISATEUR {idx}: {display_name} ({sam})")
                self.stdout.write(f"{'=' * 80}\n")
                
                # Récupérer tous les attributs de l'entrée
                all_attrs = {}
                
                # Méthode 1: Accès via les propriétés de l'objet entry
                self.stdout.write("📋 Attributs disponibles (via propriétés):")
                entry_attrs_list = []
                if hasattr(entry, 'entry_attributes'):
                    # entry_attributes est une liste de tuples (nom_attribut, valeur)
                    for attr_tuple in entry.entry_attributes:
                        if isinstance(attr_tuple, tuple) and len(attr_tuple) >= 1:
                            attr_name = attr_tuple[0]
                            entry_attrs_list.append(attr_name)
                
                # Méthode 2: Accès direct via les propriétés de l'objet
                known_attrs = [
                    'sAMAccountName', 'mail', 'givenName', 'sn', 'displayName',
                    'userPrincipalName', 'distinguishedName', 'cn', 'title',
                    'department', 'telephoneNumber', 'mobile', 'employeeID',
                    'employeeNumber', 'thumbnailPhoto', 'memberOf', 'proxyAddresses',
                    'userAccountControl', 'whenCreated', 'whenChanged', 'lastLogon',
                    'badPwdCount', 'pwdLastSet', 'accountExpires', 'description',
                    'physicalDeliveryOfficeName', 'streetAddress', 'l', 'st',
                    'postalCode', 'c', 'co', 'company', 'division', 'manager',
                    'directReports', 'assistant', 'otherTelephone', 'otherMobile',
                    'otherPager', 'facsimileTelephoneNumber', 'homePhone', 'pager',
                    'ipPhone', 'info', 'notes', 'objectClass', 'objectCategory',
                    'objectGUID', 'objectSid', 'primaryGroupID', 'profilePath',
                    'scriptPath', 'homeDirectory', 'homeDrive', 'logonHours',
                    'logonWorkstation', 'userWorkstations', 'msDS-UserPasswordExpiryTimeComputed',
                    'lastLogonTimestamp', 'lockoutTime', 'servicePrincipalName',
                    'userCertificate', 'userParameters', 'userSharedFolder',
                    'userSharedFolderOther', 'wWWHomePage', 'url', 'otherFacsimileTelephoneNumber'
                ]
                
                found_attrs = {}
                for attr_name in known_attrs:
                    try:
                        if hasattr(entry, attr_name):
                            attr_value = getattr(entry, attr_name)
                            if attr_value is not None:
                                if hasattr(attr_value, 'value'):
                                    value = attr_value.value
                                elif hasattr(attr_value, 'values'):
                                    value = attr_value.values
                                else:
                                    value = attr_value
                                
                                # Formater la valeur pour l'affichage
                                if isinstance(value, bytes):
                                    value_str = f"<bytes: {len(value)} bytes>"
                                elif isinstance(value, list):
                                    if len(value) > 3:
                                        value_str = f"[{len(value)} valeurs] {value[:3]}..."
                                    else:
                                        value_str = str(value)
                                else:
                                    value_str = str(value)
                                
                                found_attrs[attr_name] = value_str
                                all_attrs[attr_name] = value
                    except Exception as e:
                        pass
                
                # Afficher les attributs trouvés
                if found_attrs:
                    for attr_name, attr_value in sorted(found_attrs.items()):
                        # Limiter la longueur de la valeur pour l'affichage
                        display_value = str(attr_value)
                        if len(display_value) > 100:
                            display_value = display_value[:100] + "..."
                        self.stdout.write(f"  ✓ {attr_name:40} = {display_value}")
                else:
                    self.stdout.write("  (Aucun attribut standard trouvé)")
                
                # Méthode 3: Accès via conn.response pour voir tous les attributs bruts
                self.stdout.write(f"\n📋 Analyse des attributs bruts depuis conn.response:")
                if conn.response:
                    for resp in conn.response:
                        if 'dn' in resp and resp['dn'] == str(entry.entry_dn):
                            # Afficher les clés disponibles
                            if 'attributes' in resp:
                                attrs_keys = list(resp['attributes'].keys()) if isinstance(resp['attributes'], dict) else []
                                self.stdout.write(f"  Attributs dans 'attributes': {len(attrs_keys)}")
                                for key in sorted(attrs_keys)[:20]:  # Limiter à 20 pour l'affichage
                                    self.stdout.write(f"    - {key}")
                                if len(attrs_keys) > 20:
                                    self.stdout.write(f"    ... et {len(attrs_keys) - 20} autres")
                            
                            if 'raw_attributes' in resp:
                                raw_attrs_keys = list(resp['raw_attributes'].keys()) if isinstance(resp['raw_attributes'], dict) else []
                                self.stdout.write(f"  Attributs dans 'raw_attributes': {len(raw_attrs_keys)}")
                                for key in sorted(raw_attrs_keys)[:20]:  # Limiter à 20 pour l'affichage
                                    self.stdout.write(f"    - {key}")
                                if len(raw_attrs_keys) > 20:
                                    self.stdout.write(f"    ... et {len(raw_attrs_keys) - 20} autres")
                            
                            break
                
                # Si on a un utilisateur spécifique, afficher plus de détails
                if sample_user and idx == 1:
                    self.stdout.write(f"\n🔍 Détails complets pour {sam}:")
                    self.stdout.write(f"  DN: {entry.entry_dn}")
                    
                    # Essayer d'accéder à tous les attributs possibles
                    self.stdout.write(f"\n📝 Liste complète des attributs accessibles:")
                    try:
                        # Utiliser get_info pour obtenir les attributs disponibles
                        if hasattr(entry, '_entry_attributes'):
                            for attr_name in sorted(entry._entry_attributes.keys()):
                                self.stdout.write(f"    - {attr_name}")
                    except:
                        pass
            
            conn.unbind()
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ Analyse terminée"))
            self.stdout.write("\n💡 Astuce: Utilisez --sample-user <sAMAccountName> pour analyser un utilisateur spécifique")
            self.stdout.write("💡 Astuce: Utilisez --all-attributes pour récupérer tous les attributs (peut être long)")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())


