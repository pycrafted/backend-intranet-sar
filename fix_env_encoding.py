#!/usr/bin/env python
"""
Script pour corriger l'encodage du fichier .env
Convertit le fichier .env de Windows-1252/Latin-1 vers UTF-8
"""
import os
import sys
from pathlib import Path

def fix_env_encoding(env_file_path='.env'):
    """
    Convertit le fichier .env vers UTF-8
    """
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        print(f"❌ Erreur : Le fichier {env_file_path} n'existe pas")
        return False
    
    print(f"📖 Lecture du fichier {env_file_path}...")
    
    # Essayer différents encodages
    encodings_to_try = ['utf-8', 'windows-1252', 'latin-1', 'cp1252']
    content = None
    detected_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(env_path, 'r', encoding=encoding) as f:
                content = f.read()
            detected_encoding = encoding
            print(f"✅ Fichier lu avec l'encodage : {encoding}")
            break
        except UnicodeDecodeError as e:
            print(f"⚠️  Encodage {encoding} a échoué : {e}")
            continue
    
    if content is None:
        print("❌ Impossible de lire le fichier avec les encodages testés")
        return False
    
    # Créer une sauvegarde
    backup_path = env_path.with_suffix('.env.backup')
    print(f"💾 Création d'une sauvegarde : {backup_path}")
    try:
        with open(env_path, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
    except Exception as e:
        print(f"⚠️  Impossible de créer la sauvegarde : {e}")
    
    # Réécrire en UTF-8
    print(f"🔄 Conversion vers UTF-8...")
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fichier converti avec succès en UTF-8")
        print(f"💾 Sauvegarde disponible dans : {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture : {e}")
        return False

if __name__ == '__main__':
    env_file = sys.argv[1] if len(sys.argv) > 1 else '.env'
    success = fix_env_encoding(env_file)
    sys.exit(0 if success else 1)

