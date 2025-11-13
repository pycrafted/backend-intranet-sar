# Plan d'Implémentation : Monitoring Grafana + Prometheus
## Intranet SAR - Windows Server 2022

**Date de création** : 2025-01-13  
**Objectif** : Monitorer les ressources système (CPU, RAM, Disque) en temps réel pour identifier les surcharges et optimiser les ressources du serveur Windows.

---

## 🎯 Objectifs Prioritaires

### Métriques Essentielles à Monitorer
1. **CPU** : Utilisation globale et par processus (Django, PostgreSQL, Memurai)
2. **RAM** : Consommation totale et par service
3. **Disque** : Espace libre, I/O (lecture/écriture)

### Objectifs Secondaires (Phase 2)
- Temps de réponse API Django
- Connexions base de données
- Utilisateurs connectés simultanément

---

## 📋 Architecture Technique

### Composants à Installer

#### 1. Prometheus
- **Rôle** : Collecte et stockage des métriques
- **Version** : Dernière version stable
- **Installation** : Service Windows natif
- **Port** : 9090 (par défaut)
- **Stockage** : Base de données time-series locale

#### 2. Grafana
- **Rôle** : Visualisation des métriques
- **Version** : Dernière version stable
- **Installation** : Service Windows natif
- **Port** : 3000 (ou autre si conflit avec frontend)
- **Authentification** : Admin par défaut (à sécuriser)

#### 3. Windows Exporter
- **Rôle** : Exporter les métriques système Windows
- **Version** : Dernière version stable
- **Installation** : Service Windows
- **Port** : 9182 (par défaut)
- **Métriques** : CPU, RAM, Disque, Réseau, Processus

---

## 🔧 Étapes d'Implémentation

### Phase 1 : Installation et Configuration de Base

#### Étape 1.1 : Installation de Prometheus
- [ ] Télécharger Prometheus pour Windows
- [ ] Créer le répertoire d'installation (`C:\Prometheus`)
- [ ] Configurer `prometheus.yml` :
  - Scrape interval : 15 secondes
  - Retention : 30 jours
  - Cible : Windows Exporter (localhost:9182)
- [ ] Créer un service Windows pour Prometheus
- [ ] Configurer le démarrage automatique
- [ ] Tester l'accès sur http://localhost:9090

#### Étape 1.2 : Installation de Windows Exporter
- [ ] Télécharger Windows Exporter
- [ ] Installer comme service Windows
- [ ] Configurer les collectors :
  - `cpu` : Métriques CPU
  - `memory` : Métriques RAM
  - `logical_disk` : Métriques disque
  - `process` : Métriques par processus
- [ ] Vérifier l'exposition des métriques sur http://localhost:9182/metrics
- [ ] Configurer le démarrage automatique

#### Étape 1.3 : Installation de Grafana
- [ ] Télécharger Grafana pour Windows
- [ ] Installer comme service Windows
- [ ] Configurer le port (3000 ou autre si conflit)
- [ ] Accéder à l'interface : http://localhost:3000
- [ ] Configurer l'authentification admin (changer le mot de passe par défaut)
- [ ] Configurer le démarrage automatique

#### Étape 1.4 : Configuration Prometheus comme Source de Données
- [ ] Dans Grafana, ajouter Prometheus comme data source
- [ ] URL : http://localhost:9090
- [ ] Tester la connexion
- [ ] Vérifier l'accès aux métriques

---

### Phase 2 : Création des Dashboards

#### Dashboard 1 : Vue d'Ensemble Système
**Nom** : `SAR - Vue d'Ensemble Système`

**Panneaux à créer** :
1. **CPU Global**
   - Type : Graph (time series)
   - Métrique : `100 - (avg by (instance) (rate(windows_cpu_time_total{mode="idle"}[5m])) * 100)`
   - Alerte : > 80% pendant 5 minutes
   - Couleur : Rouge si > 80%, Orange si > 60%, Vert sinon

2. **CPU par Processus (Top 5)**
   - Type : Graph (time series)
   - Métrique : `topk(5, rate(windows_process_cpu_time_total[5m]))`
   - Afficher : Django, PostgreSQL, Memurai, autres processus

3. **RAM Totale**
   - Type : Stat
   - Métrique : `windows_cs_physical_memory_bytes`
   - Format : Bytes (GB)

4. **RAM Utilisée**
   - Type : Graph (time series)
   - Métrique : `(windows_cs_physical_memory_bytes - windows_os_physical_memory_free_bytes) / windows_cs_physical_memory_bytes * 100`
   - Alerte : > 85% pendant 5 minutes
   - Couleur : Rouge si > 85%, Orange si > 70%, Vert sinon

5. **RAM Disponible**
   - Type : Stat
   - Métrique : `windows_os_physical_memory_free_bytes`
   - Format : Bytes (GB)

6. **RAM par Processus (Top 5)**
   - Type : Graph (time series)
   - Métrique : `topk(5, windows_process_working_set_private_bytes)`
   - Afficher : Django, PostgreSQL, Memurai

7. **Disque - Espace Libre (C:)**
   - Type : Gauge
   - Métrique : `(windows_logical_disk_size_bytes{volume="C:"} - windows_logical_disk_free_bytes{volume="C:"}) / windows_logical_disk_size_bytes{volume="C:"} * 100`
   - Alerte : < 10% libre
   - Couleur : Rouge si < 10%, Orange si < 20%, Vert sinon

8. **Disque - Espace Total (C:)**
   - Type : Stat
   - Métrique : `windows_logical_disk_size_bytes{volume="C:"}`
   - Format : Bytes (GB)

9. **Disque - I/O Lecture**
   - Type : Graph (time series)
   - Métrique : `rate(windows_logical_disk_read_bytes_total{volume="C:"}[5m])`
   - Format : Bytes/sec (MB/s)

10. **Disque - I/O Écriture**
    - Type : Graph (time series)
    - Métrique : `rate(windows_logical_disk_write_bytes_total{volume="C:"}[5m])`
    - Format : Bytes/sec (MB/s)

#### Dashboard 2 : Détails CPU
**Nom** : `SAR - Détails CPU`

**Panneaux à créer** :
- CPU par core (si multi-core)
- CPU par processus Django
- CPU par processus PostgreSQL
- CPU par processus Memurai
- Historique CPU (24h, 7j, 30j)

#### Dashboard 3 : Détails RAM
**Nom** : `SAR - Détails RAM`

**Panneaux à créer** :
- Évolution RAM totale (graphique)
- RAM utilisée vs disponible (graphique empilé)
- Top 10 processus consommateurs de RAM
- RAM par service (Django, PostgreSQL, Memurai)
- Historique RAM (24h, 7j, 30j)

#### Dashboard 4 : Détails Disque
**Nom** : `SAR - Détails Disque`

**Panneaux à créer** :
- Espace utilisé par volume (C:, D:, etc.)
- Taux d'utilisation disque (%)
- I/O Lecture/Écriture par volume
- Prédiction d'espace (tendance)
- Alertes disque

---

### Phase 3 : Configuration des Alertes

#### Alerte 1 : CPU Élevé
- **Condition** : CPU > 80% pendant 5 minutes
- **Notification** : Email (optionnel)
- **Message** : "CPU du serveur SAR à 80%+ depuis 5 minutes. Vérifier les processus."

#### Alerte 2 : RAM Critique
- **Condition** : RAM utilisée > 85% pendant 5 minutes
- **Notification** : Email (optionnel)
- **Message** : "RAM du serveur SAR à 85%+ depuis 5 minutes. Risque de ralentissement."

#### Alerte 3 : Disque Presque Plein
- **Condition** : Espace libre < 10% sur C:
- **Notification** : Email (optionnel)
- **Message** : "Disque C: du serveur SAR à moins de 10% d'espace libre. Nettoyage urgent requis."

#### Alerte 4 : Disque Critique
- **Condition** : Espace libre < 5% sur C:
- **Notification** : Email (optionnel)
- **Message** : "URGENT : Disque C: du serveur SAR à moins de 5% d'espace libre."

---

## 📁 Structure des Fichiers

```
backend-intranet-sar/
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml          # Configuration Prometheus
│   │   ├── alerts.yml              # Règles d'alertes (optionnel)
│   │   └── README.md               # Documentation Prometheus
│   ├── grafana/
│   │   ├── dashboards/             # Exports de dashboards JSON
│   │   │   ├── vue-ensemble.json
│   │   │   ├── details-cpu.json
│   │   │   ├── details-ram.json
│   │   │   └── details-disque.json
│   │   └── README.md               # Documentation Grafana
│   └── scripts/
│       ├── install-prometheus.ps1  # Script d'installation Prometheus
│       ├── install-windows-exporter.ps1  # Script d'installation Windows Exporter
│       ├── install-grafana.ps1     # Script d'installation Grafana
│       ├── configure-prometheus.ps1  # Script de configuration
│       └── start-monitoring.ps1    # Script de démarrage des services
```

---

## 🔐 Sécurité

### Prometheus
- [ ] Ne pas exposer sur Internet (localhost uniquement)
- [ ] Configurer un firewall si nécessaire
- [ ] Limiter l'accès réseau

### Grafana
- [ ] Changer le mot de passe admin par défaut
- [ ] Configurer l'authentification (optionnel : LDAP/Active Directory)
- [ ] Ne pas exposer sur Internet (localhost ou VPN uniquement)
- [ ] Configurer HTTPS si accès externe nécessaire

---

## 📊 Métriques Prometheus à Utiliser

### CPU
```
# CPU global (%)
100 - (avg by (instance) (rate(windows_cpu_time_total{mode="idle"}[5m])) * 100)

# CPU par processus
rate(windows_process_cpu_time_total{process="python.exe"}[5m])
rate(windows_process_cpu_time_total{process="postgres.exe"}[5m])
rate(windows_process_cpu_time_total{process="memurai.exe"}[5m])
```

### RAM
```
# RAM totale
windows_cs_physical_memory_bytes

# RAM utilisée (%)
(windows_cs_physical_memory_bytes - windows_os_physical_memory_free_bytes) / windows_cs_physical_memory_bytes * 100

# RAM par processus
windows_process_working_set_private_bytes{process="python.exe"}
windows_process_working_set_private_bytes{process="postgres.exe"}
windows_process_working_set_private_bytes{process="memurai.exe"}
```

### Disque
```
# Espace utilisé (%)
(windows_logical_disk_size_bytes{volume="C:"} - windows_logical_disk_free_bytes{volume="C:"}) / windows_logical_disk_size_bytes{volume="C:"} * 100

# Espace libre (bytes)
windows_logical_disk_free_bytes{volume="C:"}

# I/O Lecture
rate(windows_logical_disk_read_bytes_total{volume="C:"}[5m])

# I/O Écriture
rate(windows_logical_disk_write_bytes_total{volume="C:"}[5m])
```

---

## 🚀 Scripts PowerShell à Créer

### 1. `install-prometheus.ps1`
- Téléchargement automatique
- Extraction dans `C:\Prometheus`
- Création du service Windows
- Configuration de base

### 2. `install-windows-exporter.ps1`
- Téléchargement automatique
- Installation comme service
- Configuration des collectors
- Démarrage du service

### 3. `install-grafana.ps1`
- Téléchargement automatique
- Installation comme service
- Configuration du port
- Démarrage du service

### 4. `configure-prometheus.ps1`
- Configuration de `prometheus.yml`
- Ajout de Windows Exporter comme target
- Redémarrage du service

### 5. `start-monitoring.ps1`
- Démarrage de tous les services
- Vérification de l'état
- Affichage des URLs d'accès

---

## ✅ Checklist de Validation

### Installation
- [ ] Prometheus accessible sur http://localhost:9090
- [ ] Windows Exporter expose les métriques sur http://localhost:9182/metrics
- [ ] Grafana accessible sur http://localhost:3000
- [ ] Prometheus configuré comme source de données dans Grafana

### Dashboards
- [ ] Dashboard "Vue d'Ensemble" créé et fonctionnel
- [ ] Dashboard "Détails CPU" créé et fonctionnel
- [ ] Dashboard "Détails RAM" créé et fonctionnel
- [ ] Dashboard "Détails Disque" créé et fonctionnel
- [ ] Toutes les métriques s'affichent correctement

### Alertes
- [ ] Alerte CPU configurée et testée
- [ ] Alerte RAM configurée et testée
- [ ] Alerte Disque configurée et testée
- [ ] Notifications fonctionnelles (si configurées)

### Services Windows
- [ ] Tous les services démarrent automatiquement
- [ ] Services redémarrent en cas d'erreur
- [ ] Logs accessibles et lisibles

---

## 📝 Notes Importantes

1. **Ports à vérifier** :
   - Prometheus : 9090
   - Grafana : 3000 (ou autre si conflit avec frontend)
   - Windows Exporter : 9182

2. **Conflits potentiels** :
   - Grafana sur port 3000 peut entrer en conflit avec le frontend Next.js
   - Solution : Changer le port Grafana (ex: 3002)

3. **Performance** :
   - Prometheus consomme peu de ressources
   - Grafana consomme peu de ressources
   - Windows Exporter consomme très peu de ressources

4. **Retention des données** :
   - Par défaut : 15 jours (ajustable)
   - Pour 30 jours : configurer `--storage.tsdb.retention.time=30d`

5. **Backup** :
   - Exporter les dashboards Grafana en JSON
   - Sauvegarder la configuration Prometheus
   - Sauvegarder les règles d'alertes

---

## 🎯 Prochaines Étapes Après Implémentation

1. **Phase 2** : Ajouter les métriques Django (temps de réponse API)
2. **Phase 3** : Ajouter les métriques PostgreSQL (connexions, requêtes lentes)
3. **Phase 4** : Ajouter les métriques Redis/Memurai
4. **Phase 5** : Ajouter les métriques utilisateurs (connexions simultanées)

---

## 📚 Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Windows Exporter GitHub](https://github.com/prometheus-community/windows_exporter)
- [Prometheus Windows Installation](https://prometheus.io/docs/prometheus/latest/installation/)

---

**Status** : ✅ Implémentation terminée - Scripts créés et prêts pour installation

## ✅ Implémentation Réalisée

### Scripts Créés

1. ✅ `monitoring/scripts/install-windows-exporter.ps1` - Installation Windows Exporter
2. ✅ `monitoring/scripts/install-prometheus.ps1` - Installation Prometheus
3. ✅ `monitoring/scripts/install-grafana.ps1` - Installation Grafana
4. ✅ `monitoring/scripts/start-monitoring.ps1` - Démarrage de tous les services
5. ✅ `monitoring/scripts/install-all.ps1` - Installation complète en une commande

### Fichiers de Configuration

1. ✅ `monitoring/prometheus/prometheus.yml` - Configuration Prometheus
2. ✅ `monitoring/README.md` - Documentation complète

### Installation Rapide

```powershell
# Option 1 : Installation complète en une commande
cd monitoring\scripts
.\install-all.ps1

# Option 2 : Installation étape par étape
.\install-windows-exporter.ps1
.\install-prometheus.ps1
.\install-grafana.ps1
.\start-monitoring.ps1
```

