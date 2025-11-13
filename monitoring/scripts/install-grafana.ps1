# Script d'installation de Grafana pour Windows
# Grafana visualise les métriques collectées par Prometheus
# Usage: .\install-grafana.ps1 [port]

param(
    [int]$Port = 3002  # Port par défaut 3002 pour éviter conflit avec frontend Next.js (3001)
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Grafana" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Vérifier si le port est disponible
$portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[ERREUR] Le port $Port est déjà utilisé!" -ForegroundColor Red
    Write-Host "  Utilisez un autre port: .\install-grafana.ps1 -Port 3003" -ForegroundColor Yellow
    exit 1
}

# Configuration
$installDir = "C:\Program Files\GrafanaLabs\grafana"
$serviceName = "Grafana"
$dataDir = "C:\ProgramData\GrafanaLabs\grafana"
$logDir = "C:\ProgramData\GrafanaLabs\grafana\logs"
$pluginsDir = Join-Path $dataDir "plugins"
$provisioningDir = Join-Path $dataDir "provisioning"

# Obtenir la dernière version de Grafana
Write-Host "[INFO] Recherche de la dernière version de Grafana..." -ForegroundColor Yellow
try {
    $latestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/grafana/grafana/releases/latest" -UseBasicParsing
    $version = $latestRelease.tag_name -replace '^v', ''
    $downloadUrl = "https://dl.grafana.com/oss/release/grafana-$version.windows-amd64.zip"
    Write-Host "[OK] Version trouvée: $version" -ForegroundColor Green
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de récupérer la dernière version, utilisation d'une version par défaut" -ForegroundColor Yellow
    $version = "10.2.2"
    $downloadUrl = "https://dl.grafana.com/oss/release/grafana-$version.windows-amd64.zip"
}

# Vérifier si Grafana est déjà installé
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Grafana est déjà installé" -ForegroundColor Yellow
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

# Créer les répertoires
Write-Host "[INFO] Création des répertoires..." -ForegroundColor Yellow
@($installDir, $dataDir, $logDir, $pluginsDir, $provisioningDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "  [OK] Cree: $_" -ForegroundColor Green
    }
}

# Télécharger Grafana
Write-Host ""
Write-Host "[INFO] Téléchargement de Grafana v$version..." -ForegroundColor Yellow
Write-Host "  URL: $downloadUrl" -ForegroundColor Gray

try {
    $tempZip = Join-Path $env:TEMP "grafana-$version.zip"
    
    # Télécharger avec progress bar
    $ProgressPreference = 'Continue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
    
    Write-Host "[OK] Téléchargement terminé" -ForegroundColor Green
    
    # Extraire l'archive
    Write-Host "[INFO] Extraction de l'archive..." -ForegroundColor Yellow
    $extractDir = Join-Path $env:TEMP "grafana-$version"
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    Expand-Archive -Path $tempZip -DestinationPath $env:TEMP -Force
    
    $extractedFolder = Join-Path $env:TEMP "grafana-$version"
    
    # Copier les fichiers vers le répertoire d'installation
    Write-Host "[INFO] Installation de Grafana..." -ForegroundColor Yellow
    Copy-Item -Path "$extractedFolder\*" -Destination $installDir -Recurse -Force
    Write-Host "[OK] Grafana installé dans: $installDir" -ForegroundColor Green
    
    # Nettoyer les fichiers temporaires
    Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $extractedFolder -Recurse -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "[ERREUR] Échec du téléchargement/installation: $_" -ForegroundColor Red
    exit 1
}

# Créer la configuration grafana.ini si elle n'existe pas
$configFile = Join-Path $dataDir "grafana.ini"
if (-not (Test-Path $configFile)) {
    Write-Host "[INFO] Création de la configuration grafana.ini..." -ForegroundColor Yellow
    
    # Copier le fichier de configuration par défaut
    $defaultConfig = Join-Path $installDir "conf\defaults.ini"
    if (Test-Path $defaultConfig) {
        Copy-Item -Path $defaultConfig -Destination $configFile -Force
    }
    
    # Modifier la configuration pour utiliser le port spécifié et écouter sur toutes les interfaces
    $configContent = Get-Content $configFile -Raw
    $configContent = $configContent -replace 'http_port = 3000', "http_port = $Port"
    $configContent = $configContent -replace ';http_addr =', "http_addr = 0.0.0.0"
    $configContent = $configContent -replace ';data = data', "data = $dataDir"
    $configContent = $configContent -replace ';logs = logs', "logs = $logDir"
    $configContent = $configContent -replace ';plugins = data/plugins', "plugins = $pluginsDir"
    
    $configContent | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
    Write-Host "[OK] Configuration créée: $configFile" -ForegroundColor Green
    Write-Host "  Port configuré: $Port" -ForegroundColor Gray
} else {
    Write-Host "[INFO] Configuration existe déjà: $configFile" -ForegroundColor Yellow
    # Mettre à jour le port et l'adresse si nécessaire
    $configContent = Get-Content $configFile -Raw
    $needsUpdate = $false
    if ($configContent -notmatch "http_port = $Port") {
        $configContent = $configContent -replace 'http_port = \d+', "http_port = $Port"
        $needsUpdate = $true
    }
    if ($configContent -notmatch "http_addr = 0.0.0.0") {
        $configContent = $configContent -replace ';http_addr =', "http_addr = 0.0.0.0"
        $needsUpdate = $true
    }
    if ($needsUpdate) {
        $configContent | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
        Write-Host "  Configuration mise à jour (port: $Port, écoute: 0.0.0.0)" -ForegroundColor Green
    }
}

# Créer le service Windows
Write-Host ""
Write-Host "[INFO] Création du service Windows avec NSSM..." -ForegroundColor Yellow

$grafanaExe = Join-Path $installDir "bin\grafana-server.exe"
$configPath = Join-Path $dataDir "grafana.ini"
$nssmExe = "C:\nssm\win64\nssm.exe"

# Arguments pour Grafana
$arguments = "--config=`"$configPath`" --homepath=`"$installDir`""

# Vérifier si NSSM est disponible
if (-not (Test-Path $nssmExe)) {
    Write-Host "[ERREUR] NSSM non trouve: $nssmExe" -ForegroundColor Red
    Write-Host "  NSSM doit etre installe pour creer le service Grafana" -ForegroundColor Yellow
    Write-Host "  Executez d'abord: .\install-prometheus-nssm.ps1" -ForegroundColor Yellow
    exit 1
}

try {
    # Supprimer le service s'il existe déjà
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "  Arret du service existant..." -ForegroundColor Gray
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Supprimer avec NSSM
        & $nssmExe remove $serviceName confirm 2>&1 | Out-Null
        
        # Supprimer avec sc.exe aussi
        & sc.exe delete $serviceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }
    
    # Créer le service avec NSSM
    Write-Host "  Installation du service avec NSSM..." -ForegroundColor Gray
    $installResult = & $nssmExe install $serviceName $grafanaExe 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Echec de l'installation avec NSSM: $installResult" -ForegroundColor Red
        exit 1
    }
    
    # Configurer les arguments
    Write-Host "  Configuration des arguments..." -ForegroundColor Gray
    & $nssmExe set $serviceName AppParameters $arguments 2>&1 | Out-Null
    
    # Configurer les autres paramètres
    Write-Host "  Configuration des autres parametres..." -ForegroundColor Gray
    & $nssmExe set $serviceName DisplayName "Grafana" 2>&1 | Out-Null
    & $nssmExe set $serviceName Description "Grafana - The open observability platform" 2>&1 | Out-Null
    & $nssmExe set $serviceName Start SERVICE_AUTO_START 2>&1 | Out-Null
    & $nssmExe set $serviceName AppDirectory $installDir 2>&1 | Out-Null
    
    # Configurer les logs
    & $nssmExe set $serviceName AppStdout (Join-Path $logDir "grafana-stdout.log") 2>&1 | Out-Null
    & $nssmExe set $serviceName AppStderr (Join-Path $logDir "grafana-stderr.log") 2>&1 | Out-Null
    
    Write-Host "[OK] Service créé avec NSSM" -ForegroundColor Green
    
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
        Write-Host "  Vérifiez les logs dans: $logDir" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Erreur lors de la création/démarrage du service: $_" -ForegroundColor Red
    exit 1
}

# Vérifier que Grafana est accessible
Write-Host ""
Write-Host "[INFO] Vérification de l'accès à Grafana..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Grafana est accessible" -ForegroundColor Green
        Write-Host "  Local: http://localhost:$Port" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${Port}" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[AVERTISSEMENT] Grafana peut avoir besoin de plus de temps pour démarrer" -ForegroundColor Yellow
    Write-Host "  Essayez d'accéder à http://${serverHost}:${Port} dans quelques secondes" -ForegroundColor Yellow
}

# Ouvrir le port dans le pare-feu
Write-Host ""
Write-Host "[INFO] Configuration du pare-feu..." -ForegroundColor Yellow
try {
    $firewallRule = Get-NetFirewallRule -DisplayName "Grafana" -ErrorAction SilentlyContinue
    if (-not $firewallRule) {
        New-NetFirewallRule -DisplayName "Grafana" -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[OK] Règle de pare-feu créée pour le port $Port" -ForegroundColor Green
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
Write-Host "  [OK] Grafana v$version installe dans: $installDir" -ForegroundColor Green
Write-Host "  [OK] Service Windows: $serviceName" -ForegroundColor Green
Write-Host "  [OK] Port: $Port" -ForegroundColor Green
Write-Host "  [OK] Donnees: $dataDir" -ForegroundColor Green
Write-Host "  [OK] Demarrage automatique: Active" -ForegroundColor Green
Write-Host ""
$serverHost = "sar-intranet.sar.sn"
Write-Host "Accès à Grafana:" -ForegroundColor Yellow
Write-Host "  URL (Local): http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  URL (Serveur): http://${serverHost}:${Port}" -ForegroundColor Cyan
Write-Host "  Utilisateur par défaut: admin" -ForegroundColor Cyan
Write-Host "  Mot de passe par défaut: admin" -ForegroundColor Cyan
Write-Host "  ⚠️  CHANGEZ LE MOT DE PASSE À LA PREMIÈRE CONNEXION!" -ForegroundColor Red
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Accédez à http://${serverHost}:${Port}" -ForegroundColor White
Write-Host "  2. Connectez-vous avec admin/admin" -ForegroundColor White
Write-Host "  3. Changez le mot de passe" -ForegroundColor White
Write-Host "  4. Ajoutez Prometheus comme source de données:" -ForegroundColor White
Write-Host "     - Configuration -> Data Sources -> Add data source" -ForegroundColor Cyan
Write-Host "     - Sélectionnez Prometheus" -ForegroundColor Cyan
Write-Host "     - URL: http://${serverHost}:9090" -ForegroundColor Cyan
Write-Host "     - Cliquez sur 'Save & Test'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  # Vérifier le statut du service:" -ForegroundColor White
Write-Host "  Get-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Redémarrer le service:" -ForegroundColor White
Write-Host "  Restart-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""

