#!/usr/bin/env python
"""
Déploiement minimal pour Render.
Évite tous les problèmes de configuration complexe.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description=""):
    """Exécute une commande et affiche le résultat"""
    print(f"Exécution: {description or command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.stdout:
            print(f"STDOUT: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERREUR: {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr.strip()}")
        return False

def deploy_render_minimal():
    """Déploiement minimal pour Render"""
    print("🚀 DÉPLOIEMENT MINIMAL RENDER")
    print("=" * 40)
    
    # Étape 1: Configuration de l'environnement
    print("\n--- Configuration Environnement ---")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings_render')
    
    # Étape 2: Test de la configuration
    print("\n--- Test Configuration ---")
    if not run_command("python test_render_config.py", "Test configuration Render"):
        print("❌ Configuration invalide")
        return False
    
    # Étape 3: Migrations
    print("\n--- Migrations ---")
    if not run_command("python manage.py makemigrations", "Création migrations"):
        print("⚠️ Erreur migrations, continuation...")
    
    if not run_command("python manage.py migrate --run-syncdb", "Application migrations"):
        print("❌ Échec migrations")
        return False
    
    # Étape 4: Fichiers statiques
    print("\n--- Fichiers Statiques ---")
    if not run_command("python manage.py collectstatic --noinput --clear", "Collecte fichiers statiques"):
        print("❌ Échec collecte fichiers statiques")
        return False
    
    # Étape 5: Vérification finale
    print("\n--- Vérification Finale ---")
    if not run_command("python manage.py check --deploy", "Vérification déploiement"):
        print("⚠️ Avertissements de déploiement détectés")
    
    print("\n✅ DÉPLOIEMENT MINIMAL RÉUSSI !")
    return True

if __name__ == "__main__":
    success = deploy_render_minimal()
    sys.exit(0 if success else 1)

