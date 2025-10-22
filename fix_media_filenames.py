#!/usr/bin/env python3
"""
Script de correction des noms de fichiers média
Ce script corrige les noms de fichiers dans la base de données pour qu'ils correspondent aux fichiers réels
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings_render')
django.setup()

from actualites.models import Article
from django.core.files.storage import default_storage

def fix_media_filenames():
    """Corrige les noms de fichiers média dans la base de données"""
    
    print("🔧 Correction des noms de fichiers média...")
    
    # Récupérer tous les articles avec des images
    articles = Article.objects.filter(image__isnull=False).exclude(image='')
    
    print(f"📰 {articles.count()} articles avec images trouvés")
    
    fixed_count = 0
    error_count = 0
    
    for article in articles:
        try:
            current_image_path = str(article.image)
            print(f"\n🔍 Article ID {article.id}: {current_image_path}")
            
            # Vérifier si le fichier existe
            if default_storage.exists(current_image_path):
                print(f"✅ Fichier existe: {current_image_path}")
                continue
            
            # Chercher le fichier correspondant dans le dossier média
            media_dir = Path("media/articles")
            if not media_dir.exists():
                print(f"❌ Dossier média non trouvé: {media_dir}")
                continue
            
            # Extraire le nom de base du fichier (sans le suffixe Django)
            base_name = current_image_path.split('/')[-1]
            # Enlever le suffixe Django (ex: _Jxa8Ucl)
            if '_' in base_name and '.' in base_name:
                name_parts = base_name.split('.')
                if len(name_parts) >= 2:
                    # Garder seulement la première partie avant le premier underscore
                    base_name = name_parts[0].split('_')[0] + '.' + '.'.join(name_parts[1:])
            
            print(f"🔍 Recherche du fichier: {base_name}")
            
            # Chercher le fichier correspondant
            found_file = None
            for file_path in media_dir.rglob("*"):
                if file_path.is_file() and file_path.name == base_name:
                    found_file = file_path
                    break
            
            if found_file:
                # Construire le nouveau chemin
                new_path = f"articles/{found_file.name}"
                print(f"✅ Fichier trouvé: {found_file} -> {new_path}")
                
                # Mettre à jour l'article
                article.image = new_path
                article.save()
                fixed_count += 1
                print(f"✅ Article {article.id} mis à jour")
            else:
                print(f"❌ Fichier non trouvé: {base_name}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Erreur pour l'article {article.id}: {e}")
            error_count += 1
    
    print(f"\n🎉 Correction terminée:")
    print(f"   - {fixed_count} articles corrigés")
    print(f"   - {error_count} erreurs")
    
    return fixed_count > 0

def list_media_files():
    """Liste tous les fichiers média disponibles"""
    
    print("📁 Fichiers média disponibles:")
    
    media_dir = Path("media/articles")
    if not media_dir.exists():
        print("❌ Dossier média non trouvé")
        return
    
    for file_path in media_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            size = file_path.stat().st_size
            print(f"  - {file_path.name} ({size} bytes)")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 SCRIPT DE CORRECTION DES NOMS DE FICHIERS MÉDIA")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_media_files()
    else:
        list_media_files()
        print("\n" + "=" * 60)
        fix_media_filenames()
    
    print("=" * 60)
