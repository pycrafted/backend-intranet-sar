#!/usr/bin/env python3
"""
Script de déploiement des fichiers média pour Render
Ce script s'assure que tous les fichiers média sont correctement déployés
"""

import os
import shutil
import sys
from pathlib import Path

def deploy_media_files():
    """Déploie tous les fichiers média vers le répertoire de production"""
    
    # Chemins
    current_dir = Path(__file__).parent
    media_dir = current_dir / "media"
    target_dir = current_dir / "media"
    
    print("🚀 Déploiement des fichiers média...")
    
    if not media_dir.exists():
        print("❌ Dossier média source non trouvé")
        return False
    
    # Créer le dossier cible s'il n'existe pas
    target_dir.mkdir(exist_ok=True)
    
    # Copier tous les fichiers média
    copied_files = 0
    for root, dirs, files in os.walk(media_dir):
        for file in files:
            if file.startswith('.'):
                continue  # Ignorer les fichiers cachés
                
            src_path = Path(root) / file
            rel_path = src_path.relative_to(media_dir)
            dst_path = target_dir / rel_path
            
            # Créer le dossier de destination si nécessaire
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            try:
                shutil.copy2(src_path, dst_path)
                print(f"✅ Copié: {rel_path}")
                copied_files += 1
            except Exception as e:
                print(f"❌ Erreur lors de la copie de {rel_path}: {e}")
    
    print(f"🎉 Déploiement terminé: {copied_files} fichiers copiés")
    return True

def verify_media_files():
    """Vérifie que tous les fichiers média sont présents"""
    
    media_dir = Path(__file__).parent / "media"
    
    print("🔍 Vérification des fichiers média...")
    
    if not media_dir.exists():
        print("❌ Dossier média non trouvé")
        return False
    
    # Lister tous les fichiers
    all_files = []
    for root, dirs, files in os.walk(media_dir):
        for file in files:
            if not file.startswith('.'):
                all_files.append(Path(root) / file)
    
    print(f"📁 {len(all_files)} fichiers trouvés:")
    for file in all_files:
        rel_path = file.relative_to(media_dir)
        size = file.stat().st_size
        print(f"  - {rel_path} ({size} bytes)")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("📦 SCRIPT DE DÉPLOIEMENT DES MÉDIAS")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_media_files()
    else:
        deploy_media_files()
        verify_media_files()
    
    print("=" * 50)

