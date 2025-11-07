"""
Management command pour analyser tous les attributs LDAP et créer un mapping complet
Usage: python manage.py analyze_ldap_fields --sample-user <sAMAccountName>
"""
from ldap3 import Server, Connection, ALL, SUBTREE
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config
import json

class Command(BaseCommand):
    help = 'Analyse tous les attributs LDAP disponibles et crée un mapping pour le modèle Employee'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-user',
            type=str,
            default='mmbaye',
            help='sAMAccountName d\'un utilisateur spécifique à analyser',
        )

    def handle(self, *args, **options):
        sample_user = options.get('sample_user')
        
        self.stdout.write("🔗 Analyse approfondie des attributs LDAP...")
        
        # Configuration LDAP
        ldap_server = getattr(settings, 'LDAP_SERVER', config('LDAP_SERVER', default='10.113.243.2'))
        ldap_port = getattr(settings, 'LDAP_PORT', config('LDAP_PORT', default=389, cast=int))
        ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', config('LDAP_BASE_DN', default='DC=sar,DC=sn'))
        ldap_bind_dn = getattr(settings, 'LDAP_BIND_DN', config('LDAP_BIND_DN', default=''))
        ldap_bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', config('LDAP_BIND_PASSWORD', default=''))
        
        if not ldap_bind_password:
            self.stdout.write(self.style.ERROR("❌ LDAP_BIND_PASSWORD non configuré"))
            return
        
        try:
            server = Server(ldap_server, port=ldap_port, get_info=ALL)
            conn = Connection(server, user=ldap_bind_dn, password=ldap_bind_password, auto_bind=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Connexion LDAP réussie"))
            
            # Rechercher l'utilisateur spécifique
            filterstr = f"(&(objectClass=user)(objectCategory=person)(sAMAccountName={sample_user}))"
            
            self.stdout.write(f"\n🔍 Recherche de l'utilisateur: {sample_user}")
            
            # Récupérer TOUS les attributs (y compris les attributs opérationnels)
            conn.search(
                search_base=ldap_base_dn,
                search_filter=filterstr,
                search_scope=SUBTREE,
                attributes=['*', '+'],  # Tous les attributs normaux + opérationnels
                size_limit=1
            )
            
            if not conn.entries:
                self.stdout.write(self.style.ERROR(f"❌ Utilisateur {sample_user} non trouvé"))
                conn.unbind()
                return
            
            entry = conn.entries[0]
            sam = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else "UNKNOWN"
            display_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else "N/A"
            
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write(f"👤 UTILISATEUR: {display_name} ({sam})")
            self.stdout.write(f"{'=' * 80}\n")
            
            # Analyser tous les attributs disponibles
            all_attributes = {}
            
            # Liste complète des attributs LDAP possibles pour les utilisateurs Active Directory
            possible_attributes = [
                # Identité de base
                'sAMAccountName', 'userPrincipalName', 'cn', 'distinguishedName', 'displayName',
                'givenName', 'sn', 'initials', 'name',
                
                # Informations de contact
                'mail', 'proxyAddresses', 'telephoneNumber', 'mobile', 'otherTelephone',
                'ipPhone', 'pager', 'facsimileTelephoneNumber', 'homePhone', 'otherMobile',
                
                # Informations professionnelles
                'title', 'department', 'company', 'description', 'physicalDeliveryOfficeName',
                'employeeID', 'employeeNumber', 'employeeType', 'employeeTypeId',
                
                # Hiérarchie
                'manager', 'directReports', 'directReportsRaw',
                
                # Adresse
                'streetAddress', 'postOfficeBox', 'l', 'st', 'postalCode', 'c', 'co',
                
                # Autres
                'wWWHomePage', 'url', 'info', 'notes', 'comment',
                'userAccountControl', 'accountExpires', 'whenCreated', 'whenChanged',
                'lastLogon', 'lastLogonTimestamp', 'pwdLastSet', 'badPwdCount',
                'memberOf', 'primaryGroupID', 'objectGUID', 'objectSid',
                'thumbnailPhoto', 'jpegPhoto', 'photo',
            ]
            
            self.stdout.write("📋 ANALYSE DES ATTRIBUTS LDAP:\n")
            
            found_attributes = {}
            for attr_name in sorted(possible_attributes):
                try:
                    if hasattr(entry, attr_name):
                        attr_value = getattr(entry, attr_name)
                        if attr_value is not None:
                            # Extraire la valeur
                            if hasattr(attr_value, 'value'):
                                value = attr_value.value
                            elif hasattr(attr_value, 'values'):
                                value = attr_value.values
                            else:
                                value = attr_value
                            
                            # Formater pour l'affichage
                            if isinstance(value, bytes):
                                value_str = f"<bytes: {len(value)} bytes>"
                                found_attributes[attr_name] = {'type': 'bytes', 'size': len(value)}
                            elif isinstance(value, list):
                                if len(value) > 0:
                                    if isinstance(value[0], bytes):
                                        value_str = f"[{len(value)} valeurs bytes]"
                                        found_attributes[attr_name] = {'type': 'list[bytes]', 'count': len(value)}
                                    else:
                                        value_str = f"[{len(value)} valeurs]: {str(value[:3])[:100]}"
                                        found_attributes[attr_name] = {'type': 'list', 'count': len(value), 'values': value[:5]}
                                else:
                                    value_str = "[]"
                                    found_attributes[attr_name] = {'type': 'list', 'count': 0}
                            else:
                                value_str = str(value)[:100]
                                found_attributes[attr_name] = {'type': 'string', 'value': value_str}
                            
                            self.stdout.write(f"  ✓ {attr_name:40} = {value_str}")
                except Exception as e:
                    pass
            
            # Analyser conn.response pour voir tous les attributs bruts
            self.stdout.write(f"\n📋 ANALYSE DES ATTRIBUTS BRUTS (conn.response):\n")
            if conn.response:
                for resp in conn.response:
                    if 'dn' in resp:
                        if 'attributes' in resp and isinstance(resp['attributes'], dict):
                            attrs_keys = list(resp['attributes'].keys())
                            self.stdout.write(f"  Attributs dans 'attributes': {len(attrs_keys)}")
                            for key in sorted(attrs_keys):
                                if key not in found_attributes:
                                    value = resp['attributes'][key]
                                    if isinstance(value, list) and len(value) > 0:
                                        if isinstance(value[0], bytes):
                                            self.stdout.write(f"    - {key}: [bytes: {len(value)} valeurs]")
                                        else:
                                            self.stdout.write(f"    - {key}: {str(value[:1])[:80]}")
                                    else:
                                        self.stdout.write(f"    - {key}: {str(value)[:80]}")
                        
                        if 'raw_attributes' in resp and isinstance(resp['raw_attributes'], dict):
                            raw_attrs_keys = list(resp['raw_attributes'].keys())
                            self.stdout.write(f"\n  Attributs dans 'raw_attributes': {len(raw_attrs_keys)}")
                            for key in sorted(raw_attrs_keys):
                                value = resp['raw_attributes'][key]
                                if isinstance(value, list) and len(value) > 0:
                                    if isinstance(value[0], bytes):
                                        self.stdout.write(f"    - {key}: [bytes: {len(value)} valeurs, {len(value[0]) if value[0] else 0} bytes par valeur]")
                                    else:
                                        self.stdout.write(f"    - {key}: {str(value[:1])[:80]}")
                                else:
                                    self.stdout.write(f"    - {key}: {str(value)[:80]}")
            
            # Créer le mapping recommandé
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write("📝 MAPPING RECOMMANDÉ POUR LE MODÈLE EMPLOYEE:")
            self.stdout.write(f"{'=' * 80}\n")
            
            mapping = {
                'first_name': 'givenName' if 'givenName' in found_attributes else 'displayName (split)',
                'last_name': 'sn' if 'sn' in found_attributes else 'displayName (split)',
                'email': 'mail' if 'mail' in found_attributes else 'userPrincipalName',
                'phone_fixed': 'telephoneNumber' if 'telephoneNumber' in found_attributes else None,
                'phone_mobile': 'mobile' if 'mobile' in found_attributes else None,
                'position_title': 'title' if 'title' in found_attributes else None,
                'department': 'department' if 'department' in found_attributes else None,
                'employee_id': None,  # À déterminer
            }
            
            # Identifier le meilleur champ pour le matricule
            self.stdout.write("🔍 RECHERCHE DU CHAMP MATRICULE:")
            matricule_candidates = []
            
            # Vérifier employeeID
            if 'employeeID' in found_attributes:
                matricule_candidates.append(('employeeID', 'Recommandé'))
            elif 'employeeNumber' in found_attributes:
                matricule_candidates.append(('employeeNumber', 'Recommandé'))
            else:
                self.stdout.write("  ⚠️  employeeID et employeeNumber non trouvés dans LDAP")
                self.stdout.write("  💡 Options possibles:")
                self.stdout.write(f"     - Utiliser sAMAccountName (username): {sam}")
                self.stdout.write("     - Créer un matricule généré (ex: SAR001, SAR002...)")
                self.stdout.write("     - Utiliser un attribut personnalisé si disponible")
            
            # Afficher le mapping
            for django_field, ldap_attr in mapping.items():
                status = "✅" if ldap_attr and ldap_attr in found_attributes else "❌"
                self.stdout.write(f"  {status} {django_field:20} ← {ldap_attr or 'NON TROUVÉ'}")
            
            # Problème identifié: matricule
            self.stdout.write(f"\n⚠️  PROBLÈME IDENTIFIÉ:")
            self.stdout.write(f"  Le champ 'employee_id' (matricule) utilise actuellement sAMAccountName")
            self.stdout.write(f"  car employeeID et employeeNumber ne sont pas présents dans LDAP.")
            self.stdout.write(f"  Solution recommandée: Utiliser sAMAccountName comme identifiant unique,")
            self.stdout.write(f"  mais créer un champ séparé 'username' dans le modèle Employee.")
            
            conn.unbind()
            
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write(self.style.SUCCESS("✅ Analyse terminée"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())


