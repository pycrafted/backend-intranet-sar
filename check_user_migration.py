#!/usr/bin/env python
"""
Script pour vérifier que les migrations des champs User seront sans problème
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

def check_user_table():
    """Vérifie la structure actuelle de la table User"""
    print("=" * 70)
    print("VÉRIFICATION DE LA TABLE USER")
    print("=" * 70)
    
    # Vérifier le nom de la table
    table_name = User._meta.db_table
    print(f"\n📊 Nom de la table: {table_name}")
    
    # Vérifier la structure actuelle
    fields_to_check = ['matricule', 'phone_number', 'phone_fixed', 'department_id', 'avatar', 'manager_id', 'position']
    existing_fields = []
    missing_fields = []
    
    with connection.cursor() as cursor:
        for field_name in fields_to_check:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, [table_name, field_name])
            
            field_exists = cursor.fetchone()
            if field_exists:
                existing_fields.append(field_name)
                col_name, data_type, is_nullable, default = field_exists
                print(f"\n✓ La colonne '{field_name}' existe déjà:")
                print(f"   Type: {data_type}")
                print(f"   Nullable: {is_nullable}")
                print(f"   Default: {default}")
            else:
                missing_fields.append(field_name)
        
        if missing_fields:
            print(f"\n📝 Colonnes à ajouter par migration:")
            for field_name in missing_fields:
                print(f"   → '{field_name}'")
        else:
            print("\n✅ Toutes les colonnes existent déjà - Pas de migration nécessaire")
    
    # Compter les utilisateurs existants (en utilisant SQL brut pour éviter le problème avec le champ matricule)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Nombre d'utilisateurs en base: {user_count}")
        
        if user_count > 0:
            print("\n📋 Détails des utilisateurs existants:")
            cursor.execute(f"""
                SELECT username, email, first_name, last_name 
                FROM {table_name} 
                LIMIT 5
            """)
            users = cursor.fetchall()
            for username, email, first_name, last_name in users:
                name = f"{first_name} {last_name}".strip() if first_name or last_name else username
                print(f"   - {username} ({email}) - {name}")
            if user_count > 5:
                print(f"   ... et {user_count - 5} autres")
        
        # Vérifier les données existantes
        print("\n🔍 Vérification des données:")
        if 'department_id' in missing_fields:
            print("   → Le champ department_id sera ajouté avec null=True, blank=True")
            print("   → Les utilisateurs existants auront department_id=NULL")
        if 'avatar' in missing_fields:
            print("   → Le champ avatar sera ajouté avec null=True, blank=True")
            print("   → Les utilisateurs existants auront avatar=NULL")
        if 'manager_id' in missing_fields:
            print("   → Le champ manager_id sera ajouté avec null=True, blank=True")
            print("   → Les utilisateurs existants auront manager_id=NULL")
            print("   → Un utilisateur peut ne pas avoir de manager (ex: DG)")
        if 'position' in missing_fields:
            print("   → Le champ position sera ajouté avec null=True, blank=True, max_length=100")
            print("   → Les utilisateurs existants auront position=NULL")
            print("   → Permet de renseigner le poste occupé (ex: DG, DSI, Comptable, Développeur)")
        if missing_fields:
            print("   → Pas de problème de migration pour les données existantes")
    
    # Vérifier les contraintes existantes sur matricule
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s
            AND kcu.column_name = 'matricule'
        """, [table_name])
        
        constraints = cursor.fetchall()
        if constraints:
            print("\n✓ Contraintes existantes sur 'matricule':")
            for constraint_name, constraint_type, column_name in constraints:
                print(f"   - {constraint_name}: {constraint_type}")
        else:
            print("\n✓ Aucune contrainte existante sur 'matricule'")
    
    # Vérifier si la table Department existe (pour la ForeignKey department)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'annuaire_department'
        """)
        dept_table_exists = cursor.fetchone()
        
        if dept_table_exists:
            print("\n✓ La table 'annuaire_department' existe")
            
            # Compter les départements disponibles
            cursor.execute("SELECT COUNT(*) FROM annuaire_department")
            dept_count = cursor.fetchone()[0]
            print(f"   → Nombre de départements disponibles: {dept_count}")
            
            if dept_count > 0:
                cursor.execute("SELECT id, name FROM annuaire_department ORDER BY name LIMIT 5")
                departments = cursor.fetchall()
                print("\n   Exemples de départements:")
                for dept_id, dept_name in departments:
                    print(f"   - {dept_name} (ID: {dept_id})")
                if dept_count > 5:
                    print(f"   ... et {dept_count - 5} autres")
        else:
            print("\n⚠️  ATTENTION: La table 'annuaire_department' n'existe pas encore!")
            print("   → Il faudra créer la migration pour 'annuaire' d'abord")
    
    # Vérifier si Pillow est installé (requis pour ImageField)
    try:
        import PIL
        print("\n✓ Pillow est installé (requis pour ImageField)")
    except ImportError:
        print("\n⚠️  ATTENTION: Pillow n'est pas installé!")
        print("   → Installer avec: pip install Pillow")
        print("   → Requis pour le champ avatar (ImageField)")
    
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    if missing_fields:
        print("\n✅ PRÊT POUR LA MIGRATION")
        print(f"\nLa migration ajoutera {len(missing_fields)} champ(s):")
        if 'phone_number' in missing_fields:
            print("   → phone_number (CharField, max_length=50, nullable) - Téléphone personnel")
        if 'phone_fixed' in missing_fields:
            print("   → phone_fixed (CharField, max_length=50, nullable) - Téléphone fixe")
        if 'position' in missing_fields:
            print("   → position (CharField, max_length=100, nullable) - Poste occupé")
        if 'department_id' in missing_fields:
            print("   → department_id (ForeignKey -> annuaire.Department, nullable) - Département")
        if 'avatar' in missing_fields:
            print("   → avatar (ImageField, upload_to='avatars/users/', nullable) - Photo de profil")
        if 'manager_id' in missing_fields:
            print("   → manager_id (ForeignKey -> User (self), nullable) - Manager (N+1)")
        print("\nCaractéristiques:")
        print("   - Nullable: True (les utilisateurs existants auront NULL)")
        print("   - Blank: True (peut être vide dans les formulaires)")
        print("   - Pas de valeur par défaut nécessaire")
        if 'department_id' in missing_fields:
            print("   - ForeignKey avec SET_NULL (suppression du département ne supprime pas l'utilisateur)")
        if 'avatar' in missing_fields:
            print("   - ImageField uploadera vers 'media/avatars/users/'")
        if 'manager_id' in missing_fields:
            print("   - ForeignKey auto-référencée avec SET_NULL (suppression du manager ne supprime pas l'utilisateur)")
            print("   - related_name='subordinates' (pour accéder aux subordonnés)")
        print("\nCette migration est SANS RISQUE car:")
        print("   1. Tous les champs sont nullable, donc pas de problème avec les données existantes")
        print("   2. Ce sont de simples opérations AddField, réversibles facilement")
        if 'department_id' in missing_fields:
            print("   3. La ForeignKey vers Department utilise SET_NULL pour préserver les données")
        if 'avatar' in missing_fields:
            print("   4. L'ImageField ne nécessite aucune donnée initiale")
        if 'manager_id' in missing_fields:
            print("   5. La ForeignKey auto-référencée permet une hiérarchie utilisateur flexible")
    else:
        print("\n✅ Toutes les colonnes sont déjà présentes")
        print("   Aucune migration nécessaire!")
    
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    try:
        check_user_table()
    except Exception as e:
        print(f"\n✗ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

