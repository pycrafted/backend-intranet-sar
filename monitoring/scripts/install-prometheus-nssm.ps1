# Script pour installer Prometheus avec NSSM (Non-Sucking Service Manager)
# NSSM gere mieux les services qui prennent du temps a demarrer
# Usage: .\install-prometheus-nssm.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation Prometheus avec NSSM" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si le script est execute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Red
    exit 1
}

$serviceName = "Prometheus"
$nssmDir = "C:\nssm"
$nssmExe = Join-Path $nssmDir "win64\nssm.exe"
$prometheusExe = "C:\Prometheus\prometheus.exe"
$configPath = "C:\Prometheus\prometheus.yml"
$dataDir = "C:\Prometheus\data"
$port = 9090
$retentionDays = 30

# Verifier si NSSM est installe
if (-not (Test-Path $nssmExe)) {
    Write-Host "[INFO] NSSM non trouve. Telechargement..." -ForegroundColor Yellow
    
    # Creer le repertoire NSSM
    if (-not (Test-Path $nssmDir)) {
        New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
    }
    
    # URL de telechargement NSSM
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = Join-Path $env:TEMP "nssm.zip"
    
    Write-Host "  Telechargement de NSSM..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
        Write-Host "[OK] Telechargement termine" -ForegroundColor Green
        
        Write-Host "  Extraction..." -ForegroundColor Gray
        $nssmExtractDir = Join-Path $env:TEMP "nssm-extract"
        Expand-Archive -Path $nssmZip -DestinationPath $nssmExtractDir -Force
        
        # Copier les fichiers
        $nssmSource = Get-ChildItem -Path $nssmExtractDir -Recurse -Filter "nssm.exe" | Where-Object { $_.Directory.Name -match "win64" } | Select-Object -First 1
        if ($nssmSource) {
            $nssmTargetDir = Join-Path $nssmDir "win64"
            New-Item -ItemType Directory -Path $nssmTargetDir -Force | Out-Null
            Copy-Item -Path $nssmSource.FullName -Destination $nssmExe -Force
            Write-Host "[OK] NSSM installe dans: $nssmExe" -ForegroundColor Green
        } else {
            Write-Host "[ERREUR] Fichier nssm.exe non trouve dans l'archive" -ForegroundColor Red
            exit 1
        }
        
        # Nettoyer
        Remove-Item -Path $nssmZip -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $nssmExtractDir -Recurse -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "[ERREUR] Echec du telechargement: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Telechargez manuellement NSSM depuis:" -ForegroundColor Yellow
        Write-Host "  https://nssm.cc/download" -ForegroundColor Cyan
        Write-Host "Et extrayez nssm.exe dans: $nssmExe" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[OK] NSSM trouve: $nssmExe" -ForegroundColor Green
}

Write-Host ""

# Verifier les fichiers Prometheus
if (-not (Test-Path $prometheusExe)) {
    Write-Host "[ERREUR] Prometheus non trouve: $prometheusExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $configPath)) {
    Write-Host "[ERREUR] Configuration non trouvee: $configPath" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Fichiers Prometheus verifies" -ForegroundColor Green
Write-Host ""

# Supprimer le service existant s'il existe
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Suppression du service existant..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Supprimer avec NSSM si cree avec NSSM
    & $nssmExe remove $serviceName confirm 2>&1 | Out-Null
    
    # Supprimer avec sc.exe
    & sc.exe delete $serviceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

# Creer le service avec NSSM
Write-Host "[INFO] Creation du service avec NSSM..." -ForegroundColor Yellow

# Installer le service
Write-Host "  Installation du service..." -ForegroundColor Gray
$installResult = & $nssmExe install $serviceName $prometheusExe 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Echec de l'installation: $installResult" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Service installe" -ForegroundColor Green

# Configurer les arguments
Write-Host "  Configuration des arguments..." -ForegroundColor Gray
$appParams = "--config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" --storage.tsdb.retention.time=${retentionDays}d --web.listen-address=0.0.0.0:$port"
& $nssmExe set $serviceName AppParameters $appParams 2>&1 | Out-Null

# Configurer les autres parametres
Write-Host "  Configuration des autres parametres..." -ForegroundColor Gray
& $nssmExe set $serviceName DisplayName "Prometheus Server" 2>&1 | Out-Null
& $nssmExe set $serviceName Description "Prometheus monitoring system and time series database" 2>&1 | Out-Null
& $nssmExe set $serviceName Start SERVICE_AUTO_START 2>&1 | Out-Null

# Configurer le repertoire de travail
& $nssmExe set $serviceName AppDirectory (Split-Path $prometheusExe -Parent) 2>&1 | Out-Null

# Configurer les logs (optionnel)
$logDir = Join-Path (Split-Path $prometheusExe -Parent) "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
& $nssmExe set $serviceName AppStdout (Join-Path $logDir "prometheus-stdout.log") 2>&1 | Out-Null
& $nssmExe set $serviceName AppStderr (Join-Path $logDir "prometheus-stderr.log") 2>&1 | Out-Null

Write-Host "[OK] Service configure" -ForegroundColor Green
Write-Host ""

# Demarrer le service
Write-Host "[INFO] Demarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "[OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre et verifier
    Write-Host "  Attente du demarrage..." -ForegroundColor Gray
    $maxWait = 30
    for ($i = 1; $i -le $maxWait; $i++) {
        Start-Sleep -Seconds 1
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Write-Host "[OK] Service demarre apres $i secondes!" -ForegroundColor Green
            break
        }
        if ($i % 5 -eq 0) {
            Write-Host "  Attente... ($i/$maxWait s) - Statut: $($service.Status)" -ForegroundColor Gray
        }
    }
    
    $finalService = Get-Service -Name $serviceName
    if ($finalService.Status -eq "Running") {
        Write-Host ""
        Write-Host "[OK] Prometheus fonctionne!" -ForegroundColor Green
        Write-Host "  Local: http://localhost:$port" -ForegroundColor Cyan
        Write-Host "  Serveur: http://sar-intranet.sar.sn:$port" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERREUR] Service toujours arrete. Statut: $($finalService.Status)" -ForegroundColor Red
        
        # Afficher les logs NSSM
        if (Test-Path (Join-Path $logDir "prometheus-stderr.log")) {
            Write-Host ""
            Write-Host "Dernieres erreurs:" -ForegroundColor Yellow
            Get-Content (Join-Path $logDir "prometheus-stderr.log") -Tail 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        }
        
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Impossible de demarrer: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation terminee!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""











