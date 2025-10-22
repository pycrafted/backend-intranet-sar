#!/usr/bin/env python3
"""
Script de récupération des migrations pour Render
Gère les conflits de tables existantes
"""

import os
import sys
import django
from django.db import connection
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings_render')
django.setup()

def check_table_exists(table_name):
    """Vérifier si une table existe dans la base de données"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def fix_migrations():
    """Corriger les migrations problématiques"""
    print("🔧 Correction des migrations...")
    
    # Vérifier les tables existantes
    tables_to_check = [
        'rag_search_log',
        'rag_documentembedding',
        'django_migrations'
    ]
    
    existing_tables = {}
    for table in tables_to_check:
        exists = check_table_exists(table)
        existing_tables[table] = exists
        print(f"   Table {table}: {'✅ Existe' if exists else '❌ N\'existe pas'}")
    
    # Si les tables principales existent, marquer les migrations comme appliquées
    if existing_tables.get('rag_search_log') and existing_tables.get('rag_documentembedding'):
        print("✅ Tables principales existent, marquage des migrations comme appliquées...")
        try:
            # Marquer la migration 0001 comme appliquée
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('mai', '0001_initial', NOW())
                    ON CONFLICT (app, name) DO NOTHING;
                """)
            print("   ✅ Migration 0001 marquée comme appliquée")
        except Exception as e:
            print(f"   ⚠️  Erreur lors du marquage: {e}")
    
    # Appliquer les migrations restantes
    print("🔄 Application des migrations restantes...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Migrations appliquées avec succès")
    except Exception as e:
        print(f"⚠️  Erreur lors des migrations: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_migrations()
    sys.exit(0 if success else 1)
