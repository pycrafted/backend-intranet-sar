# Configuration Waitress pour la Production (Windows)

**Important** : Gunicorn n'est **pas compatible avec Windows** (il utilise le module `fcntl` qui est Unix/Linux uniquement). Pour Windows, utilisez **Waitress**.

Waitress est un serveur WSGI pur Python, compatible Windows, développé par la Zope Foundation.

## Installation

Waitress est maintenant inclus dans `requirements.txt`. Pour l'installer :

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

Ou installer uniquement Waitress :

```powershell
pip install waitress
```

## Configuration

### Variables d'environnement

Vous pouvez configurer Waitress via des variables d'environnement dans votre fichier `.env` :

```env
# Port d'écoute de Waitress
WAITRESS_PORT=8001

# Nombre de threads (par défaut: 4)
WAITRESS_THREADS=4

# Timeout en secondes (par défaut: 120)
WAITRESS_TIMEOUT=120
```

### Fichier de configuration

Le fichier `waitress_config.py` contient la configuration par défaut. Vous pouvez le modifier selon vos besoins.

## Utilisation

### Démarrage

```powershell
# Méthode 1 : Utiliser le script PowerShell (recommandé)
.\start-waitress.ps1

# Méthode 2 : Commande directe avec waitress-serve
.\venv\Scripts\Activate.ps1
waitress-serve --host=0.0.0.0 --port=8001 --threads=4 master.wsgi:application

# Méthode 3 : Commande Python
python -m waitress --host=0.0.0.0 --port=8001 --threads=4 master.wsgi:application
```

### Arrêt

```powershell
# Utiliser le script PowerShell
.\stop-waitress.ps1

# Ou trouver et arrêter manuellement
netstat -ano | Select-String ":8001.*LISTENING"
Stop-Process -Id <PID> -Force
```

## Configuration pour IIS (Windows)

Si vous utilisez IIS comme reverse proxy, assurez-vous que :

1. **IIS est configuré** pour rediriger les requêtes vers Waitress (port 8001)
2. **Waitress écoute** sur `0.0.0.0:8001` (pas seulement localhost)
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

### Nombre de threads

Le nombre optimal de threads dépend de votre serveur :

- **Par défaut** : 4 threads
- **Pour I/O intensif** : 8-16 threads
- **Pour CPU intensif** : 2-4 threads

### Timeout

Le timeout par défaut est de 120 secondes. Augmentez-le si vous avez des requêtes longues.

## Comparaison Gunicorn vs Waitress

| Caractéristique | Gunicorn | Waitress |
|----------------|----------|----------|
| Compatible Windows | ❌ Non | ✅ Oui |
| Compatible Linux | ✅ Oui | ✅ Oui |
| Compatible macOS | ✅ Oui | ✅ Oui |
| Performance | Excellent | Très bon |
| Configuration | Avancée | Simple |
| Recommandé pour | Linux/macOS | Windows/Linux/macOS |

## Monitoring

### Vérifier que Waitress tourne

```powershell
# Vérifier le port
netstat -ano | Select-String ":8001.*LISTENING"

# Vérifier les processus Python
Get-Process python
```

### Logs

Waitress utilise le logging Python standard. Configurez le logging dans `settings.py` :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/waitress.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}
```

## Dépannage

### Erreur "Address already in use"

Le port est déjà utilisé. Vérifiez et arrêtez le processus :

```powershell
netstat -ano | Select-String ":8001.*LISTENING"
Stop-Process -Id <PID> -Force
```

### Erreur "Module not found"

Assurez-vous que l'environnement virtuel est activé et que Waitress est installé :

```powershell
.\venv\Scripts\Activate.ps1
pip install waitress
```

### Waitress ne démarre pas

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
- [ ] Waitress est configuré pour redémarrer automatiquement (service Windows ou Task Scheduler)
- [ ] Le pare-feu autorise le port 8001
- [ ] HTTPS est configuré (via IIS reverse proxy)

## Service Windows (Optionnel)

Pour exécuter Waitress comme un service Windows, vous pouvez utiliser :

- **NSSM** (Non-Sucking Service Manager)
- **Windows Task Scheduler**
- **IIS Application Pool** (si vous utilisez wfastcgi)

### Exemple avec NSSM

```powershell
# Installer NSSM depuis https://nssm.cc/download
# Créer le service
nssm install SAR-Backend-Waitress "C:\path\to\venv\Scripts\python.exe" "-m waitress --host=0.0.0.0 --port=8001 --threads=4 master.wsgi:application"
nssm set SAR-Backend-Waitress AppDirectory "C:\path\to\backend-intranet-sar"
nssm set SAR-Backend-Waitress DisplayName "SAR Backend Waitress"
nssm set SAR-Backend-Waitress Description "Serveur WSGI Waitress pour SAR Backend"
nssm start SAR-Backend-Waitress
```

## Migration depuis Gunicorn

Si vous aviez configuré Gunicorn, voici les équivalences :

| Gunicorn | Waitress |
|----------|----------|
| `--bind 0.0.0.0:8001` | `--host=0.0.0.0 --port=8001` |
| `--workers 4` | `--threads=4` |
| `--timeout 120` | `--channel-timeout=120` |
| `--access-logfile -` | (logging Python) |
| `--error-logfile -` | (logging Python) |

## Documentation officielle

- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/en/latest/)
- [Waitress GitHub](https://github.com/Pylons/waitress)



