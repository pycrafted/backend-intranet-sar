# Script pour corriger le service Prometheus - Version 3
# Utilise un fichier batch pour eviter les problemes de guillemets PowerShell
# Usage: .\fix-prometheus-service-v3.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction Prometheus - Version 3" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si le script est execute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Red
    exit 1
}

$serviceName = "Prometheus"
$installDir = "C:\Prometheus"
$prometheusExe = Join-Path $installDir "prometheus.exe"
$configPath = Join-Path $installDir "prometheus.yml"
$dataDir = Join-Path $installDir "data"
$port = 9090
$retentionDays = 30

# Verifier les fichiers
if (-not (Test-Path $prometheusExe)) {
    Write-Host "[ERREUR] Fichier non trouve: $prometheusExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $configPath)) {
    Write-Host "[ERREUR] Configuration non trouvee: $configPath" -ForegroundColor Red
    exit 1
}

# Creer le repertoire data s'il n'existe pas
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

Write-Host "[OK] Fichiers verifies" -ForegroundColor Green
Write-Host ""

# Arreter et supprimer le service existant
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Arret du service existant..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    Write-Host "[INFO] Suppression du service..." -ForegroundColor Yellow
    & sc.exe delete $serviceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

# Essayer avec une syntaxe simplifiee - sans guillemets dans les chemins
# Les chemins avec espaces doivent etre entre guillemets, mais pas les arguments
Write-Host "[INFO] Creation du service (syntaxe simplifiee)..." -ForegroundColor Yellow

# Methode 1: Utiliser sc.exe avec des arguments separes
# Format: "chemin\exe" arg1 arg2 arg3
# Les chemins avec espaces doivent etre entre guillemets dans les arguments aussi

$binPathArgs = @(
    "`"$prometheusExe`"",
    "--config.file=`"$configPath`"",
    "--storage.tsdb.path=`"$dataDir`"",
    "--storage.tsdb.retention.time=${retentionDays}d",
    "--web.listen-address=0.0.0.0:$port"
)
$binPathString = $binPathArgs -join " "

Write-Host "  binPath: $binPathString" -ForegroundColor Gray

# Utiliser cmd.exe pour executer sc.exe avec la bonne syntaxe
$cmdLine = "sc.exe create $serviceName binPath= `"$binPathString`" start= auto DisplayName= `"Prometheus Server`""
Write-Host "  Commande: $cmdLine" -ForegroundColor Gray

$result = cmd.exe /c $cmdLine 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Service cree" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Echec: $result" -ForegroundColor Red
    
    # Essayer une autre methode: creer un fichier de configuration de service
    Write-Host ""
    Write-Host "[INFO] Tentative avec NSSM (si disponible)..." -ForegroundColor Yellow
    
    # Verifier si NSSM est disponible
    $nssmPath = Get-Command nssm -ErrorAction SilentlyContinue
    if ($nssmPath) {
        Write-Host "  NSSM trouve, utilisation de NSSM..." -ForegroundColor Green
        & nssm install $serviceName $prometheusExe
        & nssm set $serviceName AppParameters "--config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" --storage.tsdb.retention.time=${retentionDays}d --web.listen-address=0.0.0.0:$port"
        & nssm set $serviceName DisplayName "Prometheus Server"
        & nssm set $serviceName Description "Prometheus monitoring system"
        & nssm set $serviceName Start SERVICE_AUTO_START
        Write-Host "[OK] Service cree avec NSSM" -ForegroundColor Green
    } else {
        Write-Host "  NSSM non disponible" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "[ERREUR] Impossible de creer le service avec les methodes standards" -ForegroundColor Red
        Write-Host ""
        Write-Host "Solution alternative:" -ForegroundColor Yellow
        Write-Host "  1. Installez NSSM: https://nssm.cc/download" -ForegroundColor White
        Write-Host "  2. Ou utilisez le fichier batch: .\create-prometheus-service.bat" -ForegroundColor White
        exit 1
    }
}

# Configurer le type de demarrage
Write-Host "[INFO] Configuration du type de demarrage..." -ForegroundColor Yellow
Set-Service -Name $serviceName -StartupType Automatic -ErrorAction SilentlyContinue
Write-Host "[OK] Type de demarrage configure" -ForegroundColor Green

# Demarrer le service
Write-Host ""
Write-Host "[INFO] Demarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "[OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre et verifier
    $maxWait = 10
    for ($i = 1; $i -le $maxWait; $i++) {
        Start-Sleep -Seconds 1
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Write-Host "[OK] Service demarre apres $i secondes!" -ForegroundColor Green
            break
        }
        Write-Host "  Attente... ($i/$maxWait s) - Statut: $($service.Status)" -ForegroundColor Gray
    }
    
    $finalService = Get-Service -Name $serviceName
    if ($finalService.Status -ne "Running") {
        Write-Host ""
        Write-Host "[ERREUR] Service toujours arrete. Statut: $($finalService.Status)" -ForegroundColor Red
        
        # Verifier les logs System
        Write-Host ""
        Write-Host "Verification des logs System..." -ForegroundColor Yellow
        $systemEvents = Get-EventLog -LogName System -Newest 10 -ErrorAction SilentlyContinue | Where-Object { $_.Source -eq "Service Control Manager" }
        if ($systemEvents) {
            foreach ($event in $systemEvents | Select-Object -First 3) {
                Write-Host "  [$($event.TimeGenerated)] $($event.EntryType) (ID: $($event.EventID))" -ForegroundColor $(if($event.EntryType -eq 'Error'){'Red'}else{'Yellow'})
                $msg = $event.Message
                if ($msg.Length -gt 200) { $msg = $msg.Substring(0, 200) + "..." }
                Write-Host "    $msg" -ForegroundColor Gray
            }
        }
        
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Impossible de demarrer: $_" -ForegroundColor Red
    exit 1
}

# Verifier l'acces
Write-Host ""
Write-Host "[INFO] Verification de l'acces..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:${port}" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Prometheus fonctionne!" -ForegroundColor Green
        Write-Host "  Local: http://localhost:${port}" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${port}" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[AVERTISSEMENT] Le port peut necessiter plus de temps" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminee!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""








