#!/usr/bin/env python
"""
Script pour vérifier l'état de la base de données
Vérifie les tables, leur structure et leur cohérence avec les modèles Django
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from django.db import connection

def check_table_exists(table_name):
    """Vérifie si une table existe"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def get_table_structure(table_name):
    """Récupère la structure d'une table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        return cursor.fetchall()

def check_django_migrations():
    """Vérifie l'état des migrations Django"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            ORDER BY app, name;
        """)
        return cursor.fetchall()

def check_database_health():
    """Vérifie la santé générale de la base de données"""
    print("=" * 70)
    print("VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    # 1. Vérifier si la table django_migrations existe
    print("\n1. Vérification des migrations Django...")
    django_migrations_exists = check_table_exists('django_migrations')
    if django_migrations_exists:
        print("   ✓ Table django_migrations existe")
        migrations = check_django_migrations()
        print(f"   → {len(migrations)} migrations enregistrées")
        if migrations:
            print("\n   Migrations appliquées:")
            for app, name, applied in migrations[:10]:  # Afficher les 10 premières
                status = "✓" if applied else "✗"
                print(f"   {status} {app}.{name}")
            if len(migrations) > 10:
                print(f"   ... et {len(migrations) - 10} autres")
    else:
        print("   ✗ Table django_migrations n'existe pas (base vide)")
    
    # 2. Vérifier la table rag_documentembedding
    print("\n2. Vérification de la table rag_documentembedding...")
    table_exists = check_table_exists('rag_documentembedding')
    if table_exists:
        print("   ✓ Table rag_documentembedding existe")
        structure = get_table_structure('rag_documentembedding')
        print("\n   Structure de la table:")
        expected_cols = {
            'id': 'bigint',
            'content_type': 'character varying',
            'content_id': 'integer',
            'content_text': 'text',
            'embedding': 'jsonb',
            'metadata': 'jsonb',
            'created_at': 'timestamp',
            'updated_at': 'timestamp'
        }
        
        actual_cols = {row[0]: row[1] for row in structure}
        
        print("\n   Colonnes actuelles:")
        for col_name, data_type, is_nullable, default in structure:
            nullable = "NULL" if is_nullable == 'YES' else "NOT NULL"
            print(f"   - {col_name:20} {data_type:20} {nullable}")
        
        print("\n   Vérification des colonnes attendues:")
        all_ok = True
        for col_name, expected_type in expected_cols.items():
            if col_name in actual_cols:
                actual_type = actual_cols[col_name]
                if expected_type in actual_type or actual_type in expected_type:
                    print(f"   ✓ {col_name} - OK")
                else:
                    print(f"   ⚠ {col_name} - Type différent (attendu: {expected_type}, actuel: {actual_type})")
            else:
                print(f"   ✗ {col_name} - MANQUANTE")
                all_ok = False
        
        # Vérifier les colonnes supplémentaires
        extra_cols = set(actual_cols.keys()) - set(expected_cols.keys())
        if extra_cols:
            print(f"\n   ⚠ Colonnes supplémentaires détectées: {', '.join(extra_cols)}")
        
        # Compter les enregistrements
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM rag_documentembedding")
            count = cursor.fetchone()[0]
            print(f"\n   → {count} enregistrements dans la table")
            
            if count > 0:
                cursor.execute("""
                    SELECT COUNT(*) FROM rag_documentembedding 
                    WHERE content_text IS NULL OR content_text = ''
                """)
                null_content = cursor.fetchone()[0]
                if null_content > 0:
                    print(f"   ⚠ {null_content} enregistrements sans content_text")
        
        if not all_ok:
            print("\n   ⚠ PROBLÈME: Structure incomplète ou incorrecte")
    else:
        print("   ✗ Table rag_documentembedding n'existe pas")
    
    # 3. Vérifier rag_search_log
    print("\n3. Vérification de la table rag_search_log...")
    log_exists = check_table_exists('rag_search_log')
    if log_exists:
        print("   ✓ Table rag_search_log existe")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM rag_search_log")
            count = cursor.fetchone()[0]
            print(f"   → {count} enregistrements")
    else:
        print("   ✗ Table rag_search_log n'existe pas")
    
    # 4. Vérifier l'extension pgvector
    print("\n4. Vérification de l'extension pgvector...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        pgvector_exists = cursor.fetchone()[0]
        if pgvector_exists:
            print("   ✓ Extension pgvector installée")
        else:
            print("   ✗ Extension pgvector non installée")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    issues = []
    if not django_migrations_exists:
        issues.append("Base de données vide (pas de migrations Django)")
    if not table_exists:
        issues.append("Table rag_documentembedding manquante")
    elif table_exists:
        # Vérifier si c'est l'ancienne structure (avec 'content' au lieu de 'content_text')
        structure = get_table_structure('rag_documentembedding')
        col_names = [row[0] for row in structure]
        if 'content' in col_names and 'content_text' not in col_names:
            issues.append("Table utilise l'ancien champ 'content' au lieu de 'content_text'")
        if 'content_text' not in col_names:
            issues.append("Champ 'content_text' manquant")
    
    if issues:
        print("\n⚠ PROBLÈMES DÉTECTÉS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n💡 RECOMMANDATIONS:")
        if 'content' in str(issues):
            print("   - La table utilise l'ancienne structure")
            print("   - Options:")
            print("     1. Supprimer la table et relancer les migrations")
            print("     2. Créer une migration de renommage")
        if not django_migrations_exists:
            print("   - Exécutez: python manage.py migrate")
    else:
        print("\n✓ Aucun problème détecté - Base de données OK")
    
    print("=" * 70)

if __name__ == '__main__':
    try:
        check_database_health()
    except Exception as e:
        print(f"\n✗ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


