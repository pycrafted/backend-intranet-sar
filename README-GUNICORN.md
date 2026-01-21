# Configuration Gunicorn pour la Production

**⚠️ IMPORTANT : Gunicorn n'est PAS compatible avec Windows !**

Gunicorn utilise le module `fcntl` qui est spécifique à Unix/Linux. Si vous êtes sur **Windows**, utilisez plutôt **Waitress** (voir `README-WAITRESS.md`).

Ce guide explique comment utiliser Gunicorn pour déployer le backend Django en production sur **Linux/macOS uniquement**.

## Installation

Gunicorn est déjà inclus dans `requirements.txt`. Pour l'installer :

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt
```

## Configuration

### Variables d'environnement

Vous pouvez configurer Gunicorn via des variables d'environnement dans votre fichier `.env` :

```env
# Port d'écoute de Gunicorn
GUNICORN_PORT=8001

# Nombre de workers (par défaut: CPU * 2 + 1)
GUNICORN_WORKERS=4

# Niveau de log (debug, info, warning, error, critical)
GUNICORN_LOG_LEVEL=info

# Fichiers de log (optionnel, '-' = stdout/stderr)
GUNICORN_ACCESS_LOG=-
GUNICORN_ERROR_LOG=-
```

### Fichier de configuration

Le fichier `gunicorn_config.py` contient la configuration par défaut. Vous pouvez le modifier selon vos besoins.

## Utilisation

### Démarrage

```powershell
# Méthode 1 : Utiliser le script PowerShell
.\start-gunicorn.ps1

# Méthode 2 : Commande directe
.\venv\Scripts\Activate.ps1
gunicorn master.wsgi:application --config gunicorn_config.py

# Méthode 3 : Commande directe avec paramètres
gunicorn master.wsgi:application \
    --bind 0.0.0.0:8001 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Arrêt

```powershell
# Utiliser le script PowerShell
.\stop-gunicorn.ps1

# Ou trouver et arrêter manuellement
netstat -ano | Select-String ":8001.*LISTENING"
# Puis arrêter le processus avec le PID trouvé
Stop-Process -Id <PID> -Force
```

## Configuration pour IIS (Windows)

Si vous utilisez IIS comme reverse proxy, assurez-vous que :

1. **IIS est configuré** pour rediriger les requêtes vers Gunicorn (port 8001)
2. **Gunicorn écoute** sur `0.0.0.0:8001` (pas seulement localhost)
3. **Les variables d'environnement** sont correctement configurées

### Exemple de configuration IIS

Dans votre `web.config` (frontend), vous devriez avoir une règle de rewrite vers le backend :

```xml
<rule name="API to Django" stopProcessing="true">
  <match url="^api/(.*)" />
  <action type="Rewrite" url="http://10.113.255.71:8001/api/{R:1}" />
</rule>
```

## Performance

### Nombre de workers

Le nombre optimal de workers dépend de votre serveur :

- **Formule classique** : `(2 × CPU cores) + 1`
- **Pour I/O intensif** : `(4 × CPU cores) + 1`
- **Pour CPU intensif** : `CPU cores + 1`

### Timeout

Le timeout par défaut est de 120 secondes. Augmentez-le si vous avez des requêtes longues (ex: traitement de fichiers volumineux).

## Monitoring

### Vérifier que Gunicorn tourne

```powershell
# Vérifier le port
netstat -ano | Select-String ":8001.*LISTENING"

# Vérifier les processus Python
Get-Process python
```

### Logs

Les logs sont affichés dans la console par défaut. Pour les rediriger vers des fichiers :

```env
GUNICORN_ACCESS_LOG=logs/access.log
GUNICORN_ERROR_LOG=logs/error.log
```

## Dépannage

### Erreur "Address already in use"

Le port est déjà utilisé. Vérifiez et arrêtez le processus :

```powershell
netstat -ano | Select-String ":8001.*LISTENING"
Stop-Process -Id <PID> -Force
```

### Erreur "Module not found"

Assurez-vous que l'environnement virtuel est activé et que toutes les dépendances sont installées :

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Gunicorn ne démarre pas

Vérifiez :
1. L'environnement virtuel est activé
2. Les variables d'environnement sont correctes
3. Le fichier `master/wsgi.py` existe
4. Les permissions sont correctes

## Production Checklist

- [ ] `DEBUG = False` dans `settings.py`
- [ ] `SECRET_KEY` est défini et sécurisé
- [ ] `ALLOWED_HOSTS` contient les domaines autorisés
- [ ] Les fichiers statiques sont servis correctement (WhiteNoise ou serveur web)
- [ ] Les logs sont configurés et surveillés
- [ ] Gunicorn est configuré pour redémarrer automatiquement (service Windows ou supervisor)
- [ ] Le pare-feu autorise le port 8001
- [ ] HTTPS est configuré (via IIS reverse proxy)

## Service Windows (Optionnel)

Pour exécuter Gunicorn comme un service Windows, vous pouvez utiliser :

- **NSSM** (Non-Sucking Service Manager)
- **Windows Task Scheduler**
- **IIS Application Pool** (si vous utilisez wfastcgi)

Voir `gunicorn.service.example` pour un exemple de configuration systemd (Linux).

