# 🚀 Guide de Configuration pour Nouveau PC

## ⚠️ Problèmes Courants sur Nouveau PC

### 1. Erreur : `ModuleNotFoundError: No module named 'ldap3'`

**Cause** : Les dépendances Python ne sont pas installées.

**Solution** :

```bash
# Activer l'environnement virtuel
cd backend-intranet-sar
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installer toutes les dépendances
pip install -r requirements.txt
```

### 2. Erreur : `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9`

**Cause** : Le fichier `.env` n'est pas encodé en UTF-8.

**Solution** :

```bash
# Option 1 : Utiliser le script automatique
python fix_env_encoding.py

# Option 2 : Conversion manuelle avec PowerShell
$content = Get-Content .env -Encoding Default
$content | Out-File .env -Encoding UTF8
```

### 3. Erreur Frontend : `config is not exported`

**Cause** : Cache Next.js obsolète.

**Solution** :

```bash
cd frontend-intranet-sar

# Supprimer le cache Next.js
Remove-Item -Recurse -Force .next

# Redémarrer le serveur
npm run dev
```

## 📋 Checklist d'Installation Complète

### Étape 1 : Cloner le projet
```bash
git clone <url-du-repo>
cd sar_intranet
```

### Étape 2 : Backend - Configuration Python

```bash
cd backend-intranet-sar

# Créer l'environnement virtuel (si pas déjà fait)
python -m venv venv

# Activer l'environnement virtuel
.\venv\Scripts\activate  # Windows PowerShell
# ou
venv\Scripts\activate.bat  # Windows CMD

# Installer les dépendances
pip install -r requirements.txt

# Corriger l'encodage du .env si nécessaire
python fix_env_encoding.py

# Créer le fichier .env depuis l'exemple
Copy-Item .env.example .env
# Puis éditer .env avec vos valeurs

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### Étape 3 : Frontend - Configuration Node.js

```bash
cd frontend-intranet-sar

# Installer les dépendances
npm install

# Créer le fichier .env.local depuis l'exemple
Copy-Item .env.local.example .env.local
# Puis éditer .env.local avec vos valeurs

# Vider le cache Next.js (si erreurs)
Remove-Item -Recurse -Force .next

# Démarrer le serveur de développement
npm run dev
```

### Étape 4 : Vérification

1. **Backend** : `http://localhost:8000/api/health/` doit répondre
2. **Frontend** : `http://localhost:3000` doit s'afficher

## 🔧 Dépendances Critiques

### Backend Python
- `ldap3==2.9.1` - Authentification LDAP
- `django` - Framework web
- `psycopg2` - Connexion PostgreSQL
- `redis` - Cache Redis
- `python-decouple` - Variables d'environnement

### Frontend Node.js
- `next` - Framework React
- `react` - Bibliothèque UI
- `typescript` - Typage statique

## ⚠️ Notes Importantes

1. **Encodage UTF-8** : Toujours utiliser VS Code ou Notepad++ pour éditer `.env`, jamais Notepad de Windows
2. **Environnement virtuel** : Toujours activer `venv` avant d'exécuter des commandes Python
3. **Cache Next.js** : Si des erreurs persistent, supprimer le dossier `.next`

## 🆘 En Cas de Problème

1. Vérifier que tous les modules sont installés : `pip list`
2. Vérifier l'encodage du `.env` : `python fix_env_encoding.py`
3. Vider les caches : `.next` (frontend) et `__pycache__` (backend)
4. Relire les logs d'erreur pour identifier le problème exact

