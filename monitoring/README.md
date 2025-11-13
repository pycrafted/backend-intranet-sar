# Monitoring Grafana + Prometheus pour Intranet SAR

Ce dossier contient tous les scripts et configurations nécessaires pour installer et configurer le monitoring des ressources système (CPU, RAM, Disque) sur Windows Server 2022.

## 📋 Architecture

- **Windows Exporter** : Expose les métriques système Windows (port 9182)
- **Prometheus** : Collecte et stocke les métriques (port 9090)
- **Grafana** : Visualise les métriques (port 3002)

## 🚀 Installation Rapide

### Ordre d'installation recommandé

1. **Windows Exporter** (en premier - source de métriques)
2. **Prometheus** (ensuite - collecte les métriques)
3. **Grafana** (en dernier - visualise les métriques)

### Installation complète

```powershell
# Exécuter en tant qu'administrateur
cd monitoring\scripts

# 1. Installer Windows Exporter
.\install-windows-exporter.ps1

# 2. Installer Prometheus
.\install-prometheus.ps1

# 3. Installer Grafana
.\install-grafana.ps1

# 4. Démarrer tous les services
.\start-monitoring.ps1
```

## 📝 Scripts Disponibles

### `install-windows-exporter.ps1`
Installe Windows Exporter qui expose les métriques système Windows.

**Fonctionnalités** :
- Téléchargement automatique de la dernière version
- Installation comme service Windows
- Configuration des collectors (CPU, RAM, Disque, Processus)
- Démarrage automatique au boot
- Ouverture du port 9182 dans le pare-feu

**Usage** :
```powershell
.\install-windows-exporter.ps1
```

**Vérification** :
```powershell
# Vérifier le service
Get-Service -Name windows_exporter

# Voir les métriques
Invoke-WebRequest -Uri http://sar-intranet.sar.sn:9182/metrics
```

### `install-prometheus.ps1`
Installe Prometheus qui collecte et stocke les métriques.

**Fonctionnalités** :
- Téléchargement automatique de la dernière version
- Installation dans `C:\Prometheus`
- Configuration automatique pour Windows Exporter
- Rétention des données : 30 jours
- Démarrage automatique au boot
- Ouverture du port 9090 dans le pare-feu

**Usage** :
```powershell
.\install-prometheus.ps1
```

**Vérification** :
```powershell
# Vérifier le service
Get-Service -Name Prometheus

# Accéder à l'interface web
Start-Process http://sar-intranet.sar.sn:9090
```

### `install-grafana.ps1`
Installe Grafana pour visualiser les métriques.

**Fonctionnalités** :
- Téléchargement automatique de la dernière version
- Installation dans `C:\Program Files\GrafanaLabs\grafana`
- Port par défaut : 3002 (pour éviter conflit avec frontend Next.js)
- Démarrage automatique au boot
- Ouverture du port dans le pare-feu

**Usage** :
```powershell
# Port par défaut (3002)
.\install-grafana.ps1

# Port personnalisé
.\install-grafana.ps1 -Port 3003
```

**Vérification** :
```powershell
# Vérifier le service
Get-Service -Name Grafana

# Accéder à l'interface web
Start-Process http://sar-intranet.sar.sn:3002
```

**Première connexion** :
- URL : http://sar-intranet.sar.sn:3002
- Utilisateur : `admin`
- Mot de passe : `admin`
- ⚠️ **Changez le mot de passe à la première connexion !**

### `start-monitoring.ps1`
Démarre tous les services de monitoring.

**Usage** :
```powershell
.\start-monitoring.ps1
```

## 🔧 Configuration

### Prometheus

Le fichier de configuration se trouve dans :
```
C:\Prometheus\prometheus.yml
```

Ou dans le projet :
```
monitoring/prometheus/prometheus.yml
```

### Grafana

Le fichier de configuration se trouve dans :
```
C:\ProgramData\GrafanaLabs\grafana\grafana.ini
```

## 📊 Configuration de Grafana

### 1. Ajouter Prometheus comme source de données

1. Connectez-vous à Grafana (http://sar-intranet.sar.sn:3002)
2. Allez dans **Configuration > Data Sources**
3. Cliquez sur **Add data source**
4. Sélectionnez **Prometheus**
5. Configurez :
   - **URL** : `http://sar-intranet.sar.sn:9090`
   - **Access** : Server (default)
6. Cliquez sur **Save & Test**

### 2. Créer des Dashboards

Les dashboards peuvent être créés manuellement dans Grafana ou importés depuis des fichiers JSON.

**Métriques importantes à monitorer** :

#### CPU
```
100 - (avg by (instance) (rate(windows_cpu_time_total{mode="idle"}[5m])) * 100)
```

#### RAM
```
(windows_cs_physical_memory_bytes - windows_os_physical_memory_free_bytes) / windows_cs_physical_memory_bytes * 100
```

#### Disque
```
(windows_logical_disk_size_bytes{volume="C:"} - windows_logical_disk_free_bytes{volume="C:"}) / windows_logical_disk_size_bytes{volume="C:"} * 100
```

## 🔍 Vérification et Dépannage

### Vérifier les services

```powershell
Get-Service -Name windows_exporter,Prometheus,Grafana
```

### Vérifier les ports

```powershell
# Windows Exporter
netstat -an | findstr :9182

# Prometheus
netstat -an | findstr :9090

# Grafana
netstat -an | findstr :3002
```

### Vérifier les métriques

```powershell
# Windows Exporter
Invoke-WebRequest -Uri http://sar-intranet.sar.sn:9182/metrics | Select-Object -ExpandProperty Content

# Prometheus targets
Invoke-WebRequest -Uri http://sar-intranet.sar.sn:9090/api/v1/targets | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Logs

**Prometheus** :
```
C:\Prometheus\data\
```

**Grafana** :
```
C:\ProgramData\GrafanaLabs\grafana\logs\
```

**Windows Exporter** :
```
Event Viewer > Windows Logs > Application
```

## 🛠️ Commandes Utiles

### Redémarrer un service

```powershell
Restart-Service -Name windows_exporter
Restart-Service -Name Prometheus
Restart-Service -Name Grafana
```

### Arrêter un service

```powershell
Stop-Service -Name windows_exporter
Stop-Service -Name Prometheus
Stop-Service -Name Grafana
```

### Démarrer un service

```powershell
Start-Service -Name windows_exporter
Start-Service -Name Prometheus
Start-Service -Name Grafana
```

### Voir les événements d'un service

```powershell
Get-EventLog -LogName Application -Source Prometheus -Newest 10
Get-EventLog -LogName Application -Source Grafana -Newest 10
```

## 📁 Structure des Fichiers

```
monitoring/
├── prometheus/
│   └── prometheus.yml          # Configuration Prometheus
├── grafana/
│   └── dashboards/             # Dashboards JSON (à créer)
└── scripts/
    ├── install-windows-exporter.ps1
    ├── install-prometheus.ps1
    ├── install-grafana.ps1
    └── start-monitoring.ps1
```

## ⚠️ Notes Importantes

1. **Permissions** : Tous les scripts doivent être exécutés en tant qu'administrateur
2. **Ports** : 
   - Windows Exporter : 9182
   - Prometheus : 9090
   - Grafana : 3002 (par défaut, pour éviter conflit avec frontend)
3. **Sécurité** : Ne pas exposer ces ports sur Internet sans protection
4. **Performance** : Les services consomment peu de ressources
5. **Retention** : Prometheus conserve les données pendant 30 jours par défaut

## 🎯 Prochaines Étapes

Après l'installation :

1. ✅ Installer les 3 composants (Windows Exporter, Prometheus, Grafana)
2. ✅ Configurer Prometheus comme source de données dans Grafana
3. 📊 Créer les dashboards pour CPU, RAM, Disque
4. 🔔 Configurer les alertes (optionnel)
5. 📈 Monitorer les métriques en temps réel

## 📚 Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Windows Exporter GitHub](https://github.com/prometheus-community/windows_exporter)
- [Plan d'implémentation complet](../PLAN_MONITORING_GRAFANA_PROMETHEUS.md)

---

**Status** : ✅ Scripts d'installation créés - Prêt pour déploiement

