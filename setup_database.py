#!/usr/bin/env python
"""
Script pour installer pgvector et configurer la base de données
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from django.db import connection
from django.conf import settings

def install_pgvector():
    """Installe l'extension pgvector"""
    print("📦 Installation de l'extension pgvector...")
    try:
        with connection.cursor() as cursor:
            # Vérifier si pgvector est déjà installé
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """)
            if cursor.fetchone()[0]:
                print("   ✓ Extension pgvector déjà installée")
                return True
            
            # Essayer d'installer pgvector
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                connection.commit()
                print("   ✓ Extension pgvector installée avec succès")
                return True
            except Exception as e:
                error_msg = str(e).lower()
                if 'extension "vector" does not exist' in error_msg or 'could not open extension control file' in error_msg:
                    print("   ⚠ Extension pgvector non disponible dans cette installation PostgreSQL")
                    print("   💡 Pour installer pgvector:")
                    print("      1. Téléchargez pgvector depuis: https://github.com/pgvector/pgvector")
                    print("      2. Ou utilisez une version PostgreSQL avec pgvector préinstallé")
                    print("      3. Ou continuez avec JSONB (fonctionne aussi mais moins optimal)")
                    print("\n   → Le système continuera avec JSONB pour l'embedding")
                    return False
                else:
                    raise
    except Exception as e:
        print(f"   ✗ Erreur lors de l'installation: {e}")
        print("   → Le système utilisera JSONB au lieu de VECTOR")
        return False

def apply_migrations():
    """Applique les migrations Django"""
    print("\n🔄 Application des migrations Django...")
    from django.core.management import execute_from_command_line
    
    try:
        # Créer les migrations si nécessaire
        print("   → Création des migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # D'abord, appliquer les migrations des apps Django de base (sans --run-syncdb)
        # Cela évite les problèmes de dépendances avec les tables auth_group, etc.
        print("   → Application des migrations des apps principales...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Ensuite, synchroniser les apps sans migrations si nécessaire
        print("   → Synchronisation des apps sans migrations...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        except Exception as sync_error:
            # Si la synchronisation échoue, ce n'est pas grave si les migrations principales sont OK
            print(f"   ⚠ Synchronisation partielle (non bloquant): {sync_error}")
        
        print("   ✓ Migrations appliquées avec succès")
        return True
    except Exception as e:
        print(f"   ✗ Erreur lors des migrations: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_setup():
    """Vérifie que la configuration est correcte"""
    print("\n✅ Vérification de la configuration...")
    
    checks = []
    
    # Vérifier pgvector
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        pgvector_installed = cursor.fetchone()[0]
        checks.append(("Extension pgvector", pgvector_installed))
    
    # Vérifier les tables
    tables_to_check = [
        'django_migrations',
        'rag_documentembedding',
        'rag_search_log'
    ]
    
    for table in tables_to_check:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, [table])
            exists = cursor.fetchone()[0]
            checks.append((f"Table {table}", exists))
    
    # Afficher les résultats
    all_ok = True
    for name, status in checks:
        status_symbol = "✓" if status else "✗"
        status_text = "OK" if status else "MANQUANT"
        print(f"   {status_symbol} {name}: {status_text}")
        if not status:
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale"""
    print("=" * 70)
    print("CONFIGURATION DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    # Afficher les informations de connexion
    db_config = settings.DATABASES['default']
    print(f"\n📊 Connexion à la base de données:")
    print(f"   Base: {db_config['NAME']}")
    print(f"   Host: {db_config['HOST']}")
    print(f"   Port: {db_config['PORT']}")
    print(f"   User: {db_config['USER']}")
    
    # Installer pgvector (non bloquant)
    pgvector_ok = install_pgvector()
    
    # Appliquer les migrations
    migrations_ok = apply_migrations()
    
    if not migrations_ok:
        print("\n✗ Échec de la configuration")
        sys.exit(1)
    
    # Vérifier la configuration
    verify_ok = verify_setup()
    
    print("\n" + "=" * 70)
    if verify_ok:
        print("✅ CONFIGURATION TERMINÉE AVEC SUCCÈS")
    else:
        print("⚠️  CONFIGURATION TERMINÉE AVEC AVERTISSEMENTS")
        if not pgvector_ok:
            print("\n💡 Note: pgvector n'est pas installé, mais le système")
            print("   fonctionne avec JSONB pour les embeddings.")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

