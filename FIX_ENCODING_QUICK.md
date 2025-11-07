# ⚡ Solution Rapide - Erreur d'encodage UTF-8

## 🚨 Erreur rencontrée

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 111: invalid continuation byte
```

## ✅ Solution en 3 étapes

### Étape 1 : Exécuter le script de correction

```bash
cd backend-intranet-sar
python fix_env_encoding.py
```

### Étape 2 : Vérifier que ça fonctionne

```bash
python manage.py migrate
```

### Étape 3 : Si ça ne fonctionne toujours pas

**Option A - Avec Notepad++ :**
1. Ouvrir `.env` dans Notepad++
2. Menu **Encodage** → **Convertir en UTF-8**
3. Sauvegarder (Ctrl+S)

**Option B - Avec VS Code :**
1. Ouvrir `.env` dans VS Code
2. Cliquer sur l'encodage en bas à droite
3. Choisir **"Enregistrer avec encodage"** → **UTF-8**

**Option C - Avec PowerShell :**
```powershell
$content = Get-Content .env -Encoding Default
$content | Out-File .env -Encoding UTF8
```

## 📝 Cause du problème

Le fichier `.env` a été créé/modifié avec un éditeur qui utilise **Windows-1252** au lieu de **UTF-8**.

⚠️ **Ne jamais utiliser Notepad de Windows** pour éditer `.env` !

## 🔍 Vérification

Pour vérifier que le fichier est bien en UTF-8 :

```python
python -c "with open('.env', 'r', encoding='utf-8') as f: print('✅ UTF-8 OK')"
```

