#!/usr/bin/env python
"""
Script pour supprimer complètement toutes les données du forum de la base de données.

Ce script :
1. Supprime les tables forum_forum et forum_forummessage
2. Supprime les enregistrements dans django_content_type
3. Supprime les enregistrements dans django_migrations
4. Supprime les permissions (auth_permission)
5. Supprime les logs d'administration (django_admin_log)

ATTENTION : Cette opération est IRRÉVERSIBLE !
Assurez-vous d'avoir fait une sauvegarde avant d'exécuter ce script.
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection, transaction

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')

# Initialiser Django
django.setup()


def print_header(text):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Affiche un message de succès"""
    print(f"✅ {text}")


def print_error(text):
    """Affiche un message d'erreur"""
    print(f"❌ {text}")


def print_warning(text):
    """Affiche un message d'avertissement"""
    print(f"⚠️  {text}")


def print_info(text):
    """Affiche un message d'information"""
    print(f"ℹ️  {text}")


def check_tables_exist(cursor):
    """Vérifie quelles tables forum existent dans la base de données"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'forum_%'
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]


def get_table_row_count(cursor, table_name):
    """Récupère le nombre de lignes dans une table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]
    except Exception as e:
        return None


def delete_forum_tables(cursor):
    """Supprime les tables du forum"""
    print_header("ÉTAPE 1 : Suppression des tables du forum")
    
    # Vérifier quelles tables existent
    existing_tables = check_tables_exist(cursor)
    
    if not existing_tables:
        print_info("Aucune table forum trouvée dans la base de données.")
        return
    
    print_info(f"Tables trouvées : {', '.join(existing_tables)}")
    
    # Compter les lignes avant suppression
    for table in existing_tables:
        count = get_table_row_count(cursor, table)
        if count is not None:
            print_info(f"  - {table}: {count} enregistrement(s)")
    
    # Supprimer les tables dans l'ordre des dépendances
    # ForumMessage doit être supprimé avant Forum (clé étrangère)
    tables_to_drop = ['forum_forummessage', 'forum_forum']
    
    for table in tables_to_drop:
        if table in existing_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print_success(f"Table {table} supprimée")
            except Exception as e:
                print_error(f"Erreur lors de la suppression de {table}: {e}")
    
    # Supprimer toutes les autres tables forum qui pourraient exister
    for table in existing_tables:
        if table not in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print_success(f"Table {table} supprimée")
            except Exception as e:
                print_error(f"Erreur lors de la suppression de {table}: {e}")


def delete_content_types(cursor):
    """Supprime les content types liés au forum"""
    print_header("ÉTAPE 2 : Suppression des content types")
    
    # Compter avant suppression
    cursor.execute("SELECT COUNT(*) FROM django_content_type WHERE app_label = 'forum';")
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print_info("Aucun content type forum trouvé.")
        return
    
    print_info(f"{count_before} content type(s) forum trouvé(s)")
    
    # Supprimer les content types
    cursor.execute("DELETE FROM django_content_type WHERE app_label = 'forum';")
    deleted = cursor.rowcount
    
    print_success(f"{deleted} content type(s) supprimé(s)")


def table_exists(cursor, table_name):
    """Vérifie si une table existe dans la base de données"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, [table_name])
    return cursor.fetchone()[0]


def delete_permission_references(cursor):
    """Supprime les références aux permissions dans les groupes et utilisateurs"""
    print_header("ÉTAPE 3a : Suppression des références aux permissions")
    
    # Supprimer les références dans auth_group_permissions
    if table_exists(cursor, 'auth_group_permissions'):
        cursor.execute("""
            SELECT COUNT(*) 
            FROM auth_group_permissions 
            WHERE permission_id IN (
                SELECT id FROM auth_permission 
                WHERE content_type_id IN (
                    SELECT id FROM django_content_type WHERE app_label = 'forum'
                )
            );
        """)
        count_group_perms = cursor.fetchone()[0]
        
        if count_group_perms > 0:
            print_info(f"{count_group_perms} référence(s) dans auth_group_permissions trouvée(s)")
            cursor.execute("""
                DELETE FROM auth_group_permissions 
                WHERE permission_id IN (
                    SELECT id FROM auth_permission 
                    WHERE content_type_id IN (
                        SELECT id FROM django_content_type WHERE app_label = 'forum'
                    )
                );
            """)
            deleted = cursor.rowcount
            print_success(f"{deleted} référence(s) dans auth_group_permissions supprimée(s)")
        else:
            print_info("Aucune référence dans auth_group_permissions trouvée")
    else:
        print_info("Table auth_group_permissions n'existe pas (ignorée)")
    
    # Supprimer les références dans auth_user_user_permissions
    if table_exists(cursor, 'auth_user_user_permissions'):
        cursor.execute("""
            SELECT COUNT(*) 
            FROM auth_user_user_permissions 
            WHERE permission_id IN (
                SELECT id FROM auth_permission 
                WHERE content_type_id IN (
                    SELECT id FROM django_content_type WHERE app_label = 'forum'
                )
            );
        """)
        count_user_perms = cursor.fetchone()[0]
        
        if count_user_perms > 0:
            print_info(f"{count_user_perms} référence(s) dans auth_user_user_permissions trouvée(s)")
            cursor.execute("""
                DELETE FROM auth_user_user_permissions 
                WHERE permission_id IN (
                    SELECT id FROM auth_permission 
                    WHERE content_type_id IN (
                        SELECT id FROM django_content_type WHERE app_label = 'forum'
                    )
                );
            """)
            deleted = cursor.rowcount
            print_success(f"{deleted} référence(s) dans auth_user_user_permissions supprimée(s)")
        else:
            print_info("Aucune référence dans auth_user_user_permissions trouvée")
    else:
        print_info("Table auth_user_user_permissions n'existe pas (ignorée - modèle utilisateur personnalisé possible)")
    
    # Supprimer les références dans authentication_user_user_permissions (modèle utilisateur personnalisé)
    if table_exists(cursor, 'authentication_user_user_permissions'):
        cursor.execute("""
            SELECT COUNT(*) 
            FROM authentication_user_user_permissions 
            WHERE permission_id IN (
                SELECT id FROM auth_permission 
                WHERE content_type_id IN (
                    SELECT id FROM django_content_type WHERE app_label = 'forum'
                )
            );
        """)
        count_auth_user_perms = cursor.fetchone()[0]
        
        if count_auth_user_perms > 0:
            print_info(f"{count_auth_user_perms} référence(s) dans authentication_user_user_permissions trouvée(s)")
            cursor.execute("""
                DELETE FROM authentication_user_user_permissions 
                WHERE permission_id IN (
                    SELECT id FROM auth_permission 
                    WHERE content_type_id IN (
                        SELECT id FROM django_content_type WHERE app_label = 'forum'
                    )
                );
            """)
            deleted = cursor.rowcount
            print_success(f"{deleted} référence(s) dans authentication_user_user_permissions supprimée(s)")
        else:
            print_info("Aucune référence dans authentication_user_user_permissions trouvée")
    else:
        print_info("Table authentication_user_user_permissions n'existe pas (ignorée)")


def delete_permissions(cursor):
    """Supprime les permissions liées au forum"""
    print_header("ÉTAPE 3b : Suppression des permissions")
    
    # Compter avant suppression
    cursor.execute("""
        SELECT COUNT(*) 
        FROM auth_permission 
        WHERE content_type_id IN (
            SELECT id FROM django_content_type WHERE app_label = 'forum'
        );
    """)
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print_info("Aucune permission forum trouvée (normal si content types déjà supprimés).")
        return
    
    print_info(f"{count_before} permission(s) forum trouvée(s)")
    
    # Supprimer les permissions
    cursor.execute("""
        DELETE FROM auth_permission 
        WHERE content_type_id IN (
            SELECT id FROM django_content_type WHERE app_label = 'forum'
        );
    """)
    deleted = cursor.rowcount
    
    print_success(f"{deleted} permission(s) supprimée(s)")


def delete_admin_logs(cursor):
    """Supprime les logs d'administration liés au forum"""
    print_header("ÉTAPE 4 : Suppression des logs d'administration")
    
    # Compter avant suppression
    cursor.execute("""
        SELECT COUNT(*) 
        FROM django_admin_log 
        WHERE content_type_id IN (
            SELECT id FROM django_content_type WHERE app_label = 'forum'
        );
    """)
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print_info("Aucun log d'administration forum trouvé (normal si content types déjà supprimés).")
        return
    
    print_info(f"{count_before} log(s) d'administration forum trouvé(s)")
    
    # Supprimer les logs
    cursor.execute("""
        DELETE FROM django_admin_log 
        WHERE content_type_id IN (
            SELECT id FROM django_content_type WHERE app_label = 'forum'
        );
    """)
    deleted = cursor.rowcount
    
    print_success(f"{deleted} log(s) supprimé(s)")


def delete_migrations(cursor):
    """Supprime les enregistrements de migrations liés au forum"""
    print_header("ÉTAPE 5 : Suppression des enregistrements de migrations")
    
    # Compter avant suppression
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'forum';")
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print_info("Aucun enregistrement de migration forum trouvé.")
        return
    
    print_info(f"{count_before} enregistrement(s) de migration forum trouvé(s)")
    
    # Afficher les migrations qui seront supprimées
    cursor.execute("SELECT name FROM django_migrations WHERE app = 'forum' ORDER BY name;")
    migrations = [row[0] for row in cursor.fetchall()]
    print_info(f"Migrations : {', '.join(migrations)}")
    
    # Supprimer les migrations
    cursor.execute("DELETE FROM django_migrations WHERE app = 'forum';")
    deleted = cursor.rowcount
    
    print_success(f"{deleted} enregistrement(s) de migration supprimé(s)")


def verify_cleanup(cursor):
    """Vérifie que le nettoyage a été effectué correctement"""
    print_header("VÉRIFICATION DU NETTOYAGE")
    
    # Vérifier les tables
    remaining_tables = check_tables_exist(cursor)
    if remaining_tables:
        print_warning(f"Tables restantes : {', '.join(remaining_tables)}")
    else:
        print_success("Aucune table forum restante")
    
    # Vérifier les content types
    cursor.execute("SELECT COUNT(*) FROM django_content_type WHERE app_label = 'forum';")
    content_types_count = cursor.fetchone()[0]
    if content_types_count > 0:
        print_warning(f"{content_types_count} content type(s) forum restant(s)")
    else:
        print_success("Aucun content type forum restant")
    
    # Vérifier les migrations
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'forum';")
    migrations_count = cursor.fetchone()[0]
    if migrations_count > 0:
        print_warning(f"{migrations_count} enregistrement(s) de migration forum restant(s)")
    else:
        print_success("Aucun enregistrement de migration forum restant")


def main():
    """Fonction principale"""
    print_header("SCRIPT DE NETTOYAGE DU FORUM")
    print_warning("ATTENTION : Cette opération est IRRÉVERSIBLE !")
    print_warning("Toutes les données du forum seront définitivement supprimées.")
    print()
    
    # Afficher les informations de connexion
    db_config = settings.DATABASES['default']
    print_info(f"Base de données : {db_config['NAME']}")
    print_info(f"Hôte : {db_config['HOST']}")
    print_info(f"Port : {db_config['PORT']}")
    print_info(f"Utilisateur : {db_config['USER']}")
    print()
    
    # Demander confirmation
    confirmation = input("⚠️  Tapez 'OUI' pour confirmer la suppression : ")
    
    if confirmation != "OUI":
        print()
        print_warning("Opération annulée.")
        return
    
    print()
    
    try:
        with connection.cursor() as cursor:
            # Démarrer une transaction
            with transaction.atomic():
                # Étape 1 : Supprimer les références aux permissions dans les groupes et utilisateurs
                # (doit être fait AVANT de supprimer les permissions)
                delete_permission_references(cursor)
                
                # Étape 2 : Supprimer les permissions AVANT les content types
                # (car les permissions ont une FK vers content_type)
                delete_permissions(cursor)
                
                # Étape 3 : Supprimer les logs d'administration AVANT les content types
                # (car les logs ont aussi une FK vers content_type)
                delete_admin_logs(cursor)
                
                # Étape 4 : Supprimer les content types
                delete_content_types(cursor)
                
                # Étape 5 : Supprimer les tables
                delete_forum_tables(cursor)
                
                # Étape 6 : Supprimer les migrations
                delete_migrations(cursor)
                
                # Vérification finale
                verify_cleanup(cursor)
        
        print()
        print_header("NETTOYAGE TERMINÉ")
        print_success("Toutes les données du forum ont été supprimées avec succès !")
        print()
        print_info("Vous pouvez maintenant exécuter :")
        print("  python manage.py makemigrations")
        print("  python manage.py migrate")
        print()
        
    except Exception as e:
        print()
        print_error(f"Erreur lors du nettoyage : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

