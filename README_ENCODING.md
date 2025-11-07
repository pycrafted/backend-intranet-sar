# 🔧 Résolution du problème d'encodage UTF-8

## Problème

Si vous rencontrez l'erreur suivante :
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 111: invalid continuation byte
```

Cela signifie que votre fichier `.env` n'est pas encodé en UTF-8, mais probablement en **Windows-1252** ou **Latin-1**.

## Solution rapide

### Option 1 : Utiliser le script Python (Recommandé)

```bash
# Depuis le répertoire backend-intranet-sar
python fix_env_encoding.py
```

Ce script va :
1. Détecter l'encodage actuel du fichier `.env`
2. Créer une sauvegarde (`.env.backup`)
3. Convertir le fichier en UTF-8

### Option 2 : Conversion manuelle avec Notepad++

1. Ouvrez le fichier `.env` dans **Notepad++**
2. Allez dans le menu **Encodage** → **Convertir en UTF-8**
3. Sauvegardez le fichier (Ctrl+S)

### Option 3 : Conversion manuelle avec VS Code

1. Ouvrez le fichier `.env` dans **VS Code**
2. Cliquez sur l'encodage affiché en bas à droite (ex: "Windows-1252")
3. Sélectionnez **"Enregistrer avec encodage"**
4. Choisissez **"UTF-8"**

### Option 4 : Conversion avec PowerShell

```powershell
# Depuis le répertoire backend-intranet-sar
$content = Get-Content .env -Encoding Default
$content | Out-File .env -Encoding UTF8
```

## Vérification

Après la conversion, vérifiez que le fichier est bien en UTF-8 :

```bash
# Avec Python
python -c "with open('.env', 'r', encoding='utf-8') as f: print('✅ UTF-8 valide')"

# Ou avec PowerShell
[System.IO.File]::ReadAllText('.env', [System.Text.Encoding]::UTF8)
```

## Prévention

Pour éviter ce problème à l'avenir :

1. **Toujours créer les fichiers `.env` en UTF-8**
2. **Utiliser un éditeur qui supporte UTF-8** (VS Code, Notepad++, Sublime Text)
3. **Éviter Notepad de Windows** qui peut créer des fichiers en Windows-1252

## Caractères problématiques

Les caractères suivants peuvent causer des problèmes si le fichier n'est pas en UTF-8 :
- `é`, `è`, `ê`, `ë` (caractères accentués)
- `§`, `©`, `®` (symboles spéciaux)
- Caractères non-ASCII dans les mots de passe

## Note importante

⚠️ **Ne modifiez JAMAIS le fichier `.env` avec Notepad de Windows** car il peut changer l'encodage automatiquement.

