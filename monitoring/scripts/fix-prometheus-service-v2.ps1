# Script pour corriger le service Prometheus avec sc.exe
# Usage: .\fix-prometheus-service-v2.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction Prometheus avec sc.exe" -ForegroundColor Cyan
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

# Construire le binPath avec la syntaxe correcte pour sc.exe
# Format: "chemin\exe" "arg1" "arg2" "arg3"
# Les arguments avec espaces doivent etre entre guillemets
$binPath = "`"$prometheusExe`" --config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" --storage.tsdb.retention.time=${retentionDays}d --web.listen-address=0.0.0.0:$port"

Write-Host "[INFO] Creation du service avec sc.exe..." -ForegroundColor Yellow
Write-Host "  binPath: $binPath" -ForegroundColor Gray
Write-Host ""

# Utiliser sc.exe create avec la syntaxe correcte
$result = & sc.exe create $serviceName binPath= $binPath start= auto DisplayName= "Prometheus Server" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Service cree avec sc.exe" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Echec de la creation avec sc.exe" -ForegroundColor Red
    Write-Host "  Sortie: $result" -ForegroundColor Yellow
    
    # Essayer avec New-Service mais avec une syntaxe differente
    Write-Host ""
    Write-Host "[INFO] Tentative avec New-Service (syntaxe alternative)..." -ForegroundColor Yellow
    
    # Essayer sans guillemets autour de l'exe dans BinaryPathName
    $binPathAlt = "$prometheusExe --config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" --storage.tsdb.retention.time=${retentionDays}d --web.listen-address=0.0.0.0:$port"
    
    try {
        $serviceParams = @{
            Name = $serviceName
            BinaryPathName = $binPathAlt
            DisplayName = "Prometheus Server"
            StartupType = "Automatic"
            Description = "Prometheus monitoring system"
        }
        New-Service @serviceParams -ErrorAction Stop | Out-Null
        Write-Host "[OK] Service cree avec New-Service" -ForegroundColor Green
    } catch {
        Write-Host "[ERREUR] Echec avec New-Service: $_" -ForegroundColor Red
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
        $systemEvents = Get-EventLog -LogName System -Newest 10 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match "Prometheus" -or $_.Message -match "prometheus" -or ($_.Source -eq "Service Control Manager" -and $_.Message -match "109") }
        if ($systemEvents) {
            foreach ($event in $systemEvents | Select-Object -First 3) {
                Write-Host "  [$($event.TimeGenerated)] $($event.EntryType) (ID: $($event.EventID))" -ForegroundColor $(if($event.EntryType -eq 'Error'){'Red'}else{'Yellow'})
                $msg = $event.Message
                if ($msg.Length -gt 200) { $msg = $msg.Substring(0, 200) + "..." }
                Write-Host "    $msg" -ForegroundColor Gray
            }
        }
        
        # Afficher la configuration actuelle
        Write-Host ""
        Write-Host "Configuration actuelle du service:" -ForegroundColor Yellow
        $serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
        if ($serviceWmi) {
            Write-Host "  Chemin: $($serviceWmi.PathName)" -ForegroundColor White
            Write-Host "  Compte: $($serviceWmi.StartName)" -ForegroundColor White
            Write-Host "  Code d'erreur: $($serviceWmi.ExitCode)" -ForegroundColor $(if($serviceWmi.ExitCode -eq 0){"Green"}else{"Red"})
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

