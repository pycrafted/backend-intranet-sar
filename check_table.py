#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from django.db import connection

def check_table_structure():
    """Vérifie la structure de la table rag_documentembedding"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'rag_documentembedding'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print("Structure de la table rag_documentembedding:")
        print("=" * 50)
        for col_name, col_type in columns:
            print(f"  {col_name}: {col_type}")
        
        print(f"\nTotal: {len(columns)} colonnes")
        
        # Vérifier les colonnes attendues
        expected_columns = ['id', 'content', 'embedding', 'metadata', 'created_at', 'updated_at']
        actual_columns = [col[0] for col in columns]
        
        print("\nVerification des colonnes attendues:")
        for col in expected_columns:
            if col in actual_columns:
                print(f"  [OK] {col}")
            else:
                print(f"  [MISSING] {col} - MANQUANTE")

if __name__ == '__main__':
    check_table_structure()
