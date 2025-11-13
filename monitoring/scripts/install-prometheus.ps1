# Script d'installation de Prometheus pour Windows
# Prometheus collecte et stocke les métriques
# Usage: .\install-prometheus.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Prometheus" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Configuration
$installDir = "C:\Prometheus"
$serviceName = "Prometheus"
$port = 9090
$retentionDays = 30

# Obtenir la dernière version de Prometheus
Write-Host "[INFO] Recherche de la dernière version de Prometheus..." -ForegroundColor Yellow
try {
    $latestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/prometheus/prometheus/releases/latest" -UseBasicParsing
    $version = $latestRelease.tag_name -replace '^v', ''
    $downloadUrl = "https://github.com/prometheus/prometheus/releases/download/v$version/prometheus-$version.windows-amd64.zip"
    Write-Host "[OK] Version trouvée: $version" -ForegroundColor Green
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de récupérer la dernière version, utilisation d'une version par défaut" -ForegroundColor Yellow
    $version = "2.48.0"
    $downloadUrl = "https://github.com/prometheus/prometheus/releases/download/v$version/prometheus-$version.windows-amd64.zip"
}

# Vérifier si Prometheus est déjà installé
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Prometheus est déjà installé" -ForegroundColor Yellow
    Write-Host "  Service: $($existingService.DisplayName)" -ForegroundColor White
    Write-Host "  Statut: $($existingService.Status)" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Voulez-vous réinstaller? (O/N)"
    if ($response -ne 'O' -and $response -ne 'o') {
        Write-Host "[ANNULÉ] Installation annulée" -ForegroundColor Yellow
        exit 0
    }
    
    # Arrêter le service existant
    Write-Host "Arrêt du service existant..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Créer le répertoire d'installation
Write-Host "[INFO] Création du répertoire d'installation: $installDir" -ForegroundColor Yellow
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Write-Host "[OK] Répertoire créé" -ForegroundColor Green
} else {
    Write-Host "[OK] Répertoire existe déjà" -ForegroundColor Green
}

# Télécharger Prometheus
Write-Host ""
Write-Host "[INFO] Téléchargement de Prometheus v$version..." -ForegroundColor Yellow
Write-Host "  URL: $downloadUrl" -ForegroundColor Gray

try {
    $tempZip = Join-Path $env:TEMP "prometheus-$version.zip"
    
    # Télécharger avec progress bar
    $ProgressPreference = 'Continue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
    
    Write-Host "[OK] Téléchargement terminé" -ForegroundColor Green
    
    # Extraire l'archive
    Write-Host "[INFO] Extraction de l'archive..." -ForegroundColor Yellow
    $extractDir = Join-Path $env:TEMP "prometheus-$version"
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    Expand-Archive -Path $tempZip -DestinationPath $env:TEMP -Force
    
    $extractedFolder = Join-Path $env:TEMP "prometheus-$version.windows-amd64"
    
    # Copier les fichiers vers le répertoire d'installation
    Write-Host "[INFO] Installation de Prometheus..." -ForegroundColor Yellow
    Copy-Item -Path "$extractedFolder\*" -Destination $installDir -Recurse -Force
    Write-Host "[OK] Prometheus installé dans: $installDir" -ForegroundColor Green
    
    # Nettoyer les fichiers temporaires
    Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $extractedFolder -Recurse -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "[ERREUR] Échec du téléchargement/installation: $_" -ForegroundColor Red
    exit 1
}

# Créer la configuration prometheus.yml si elle n'existe pas
$configFile = Join-Path $installDir "prometheus.yml"
if (-not (Test-Path $configFile)) {
    Write-Host "[INFO] Création de la configuration prometheus.yml..." -ForegroundColor Yellow
    
    $configContent = @"
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'sar-monitor'

# Règles d'alertes (optionnel pour l'instant)
# rule_files:
#   - "alerts.yml"

# Configuration des cibles à scraper
scrape_configs:
  # Windows Exporter - métriques système Windows
  - job_name: 'windows'
    static_configs:
      - targets: ['sar-intranet.sar.sn:9182']
        labels:
          instance: 'sar-windows-server'
          environment: 'production'

  # Prometheus lui-même (métriques internes)
  - job_name: 'prometheus'
    static_configs:
      - targets: ['sar-intranet.sar.sn:9090']
        labels:
          instance: 'prometheus-server'
          environment: 'production'
"@
    
    $configContent | Out-File -FilePath $configFile -Encoding UTF8
    Write-Host "[OK] Configuration créée: $configFile" -ForegroundColor Green
} else {
    Write-Host "[INFO] Configuration existe déjà: $configFile" -ForegroundColor Yellow
    
    # Vérifier et mettre à jour si nécessaire
    $existingConfig = Get-Content $configFile -Raw
    if ($existingConfig -notmatch "sar-intranet.sar.sn:9182") {
        Write-Host "  Mise à jour de la configuration pour utiliser sar-intranet.sar.sn..." -ForegroundColor Yellow
        $existingConfig = $existingConfig -replace "localhost:9182", "sar-intranet.sar.sn:9182"
        $existingConfig = $existingConfig -replace "127.0.0.1:9182", "sar-intranet.sar.sn:9182"
        $existingConfig | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
        Write-Host "  [OK] Configuration mise à jour" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Configuration déjà correcte" -ForegroundColor Green
    }
}

# Créer le service Windows
Write-Host ""
Write-Host "[INFO] Création du service Windows..." -ForegroundColor Yellow

$prometheusExe = Join-Path $installDir "prometheus.exe"
$configPath = Join-Path $installDir "prometheus.yml"
$dataDir = Join-Path $installDir "data"
$storageArgs = "--storage.tsdb.retention.time=${retentionDays}d"

# Arguments pour Prometheus
# Écouter sur toutes les interfaces (0.0.0.0) pour permettre l'accès depuis sar-intranet.sar.sn
$arguments = "--config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" $storageArgs --web.listen-address=0.0.0.0:$port"

try {
    # Supprimer le service s'il existe déjà
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "  Arrêt du service existant..." -ForegroundColor Yellow
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        & sc.exe delete $serviceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }
    
    # Créer le nouveau service avec New-Service (plus fiable)
    Write-Host "  Création du service..." -ForegroundColor Yellow
    $serviceParams = @{
        Name = $serviceName
        BinaryPathName = "`"$prometheusExe`" $arguments"
        DisplayName = "Prometheus Server"
        StartupType = "Automatic"
        Description = "Prometheus monitoring system and time series database"
    }
    
    New-Service @serviceParams -ErrorAction Stop | Out-Null
    Write-Host "[OK] Service créé avec succès" -ForegroundColor Green
    
    # Configurer le service pour démarrer automatiquement
    Set-Service -Name $serviceName -StartupType Automatic -ErrorAction Stop
    Write-Host "[OK] Service configuré pour démarrer automatiquement" -ForegroundColor Green
    
    # Démarrer le service
    Write-Host "[INFO] Démarrage du service..." -ForegroundColor Yellow
    Start-Service -Name $serviceName -ErrorAction Stop
    Start-Sleep -Seconds 5
    
    $service = Get-Service -Name $serviceName
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service démarré avec succès" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Le service n'a pas démarré. Statut: $($service.Status)" -ForegroundColor Red
        Write-Host "  Vérifiez les logs avec: Get-EventLog -LogName Application -Source Prometheus -Newest 10" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Erreur lors de la création/démarrage du service: $_" -ForegroundColor Red
    exit 1
}

# Vérifier que Prometheus est accessible
Write-Host ""
Write-Host "[INFO] Vérification de l'accès à Prometheus..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$port" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Prometheus est accessible" -ForegroundColor Green
        Write-Host "  Local: http://localhost:$port" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${port}" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[AVERTISSEMENT] Prometheus peut avoir besoin de plus de temps pour démarrer" -ForegroundColor Yellow
        Write-Host "  Essayez d'accéder à http://${serverHost}:${port} dans quelques secondes" -ForegroundColor Yellow
}

# Ouvrir le port dans le pare-feu (optionnel)
Write-Host ""
Write-Host "[INFO] Configuration du pare-feu..." -ForegroundColor Yellow
try {
    $firewallRule = Get-NetFirewallRule -DisplayName "Prometheus" -ErrorAction SilentlyContinue
    if (-not $firewallRule) {
        New-NetFirewallRule -DisplayName "Prometheus" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[OK] Règle de pare-feu créée pour le port $port" -ForegroundColor Green
    } else {
        Write-Host "[OK] Règle de pare-feu existe déjà" -ForegroundColor Green
    }
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de configurer le pare-feu: $_" -ForegroundColor Yellow
}

# Résumé
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation terminée avec succès!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Résumé de l'installation:" -ForegroundColor Yellow
Write-Host "  ✓ Prometheus v$version installé dans: $installDir" -ForegroundColor Green
Write-Host "  ✓ Service Windows: $serviceName" -ForegroundColor Green
Write-Host "  ✓ Port: $port" -ForegroundColor Green
Write-Host "  ✓ Rétention des données: $retentionDays jours" -ForegroundColor Green
Write-Host "  ✓ Configuration: $configPath" -ForegroundColor Green
Write-Host "  ✓ Démarrage automatique: Activé" -ForegroundColor Green
Write-Host ""
$serverHost = "sar-intranet.sar.sn"
Write-Host "URLs importantes:" -ForegroundColor Yellow
Write-Host "  Interface web (Local): http://localhost:$port" -ForegroundColor Cyan
Write-Host "  Interface web (Serveur): http://${serverHost}:${port}" -ForegroundColor Cyan
Write-Host "  API: http://${serverHost}:${port}/api/v1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  # Vérifier le statut du service:" -ForegroundColor White
Write-Host "  Get-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Redémarrer le service:" -ForegroundColor White
Write-Host "  Restart-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Voir les targets configurés:" -ForegroundColor White
Write-Host "  Invoke-WebRequest -Uri 'http://sar-intranet.sar.sn:${port}/api/v1/targets' | ConvertFrom-Json | ConvertTo-Json -Depth 10" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaine étape:" -ForegroundColor Yellow
Write-Host "  Installez Grafana avec: .\install-grafana.ps1" -ForegroundColor Cyan
Write-Host ""

