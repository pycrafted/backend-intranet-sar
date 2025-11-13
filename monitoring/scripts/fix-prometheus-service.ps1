# Script pour diagnostiquer et corriger le service Prometheus
# Usage: .\fix-prometheus-service.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Diagnostic et correction Prometheus" -ForegroundColor Cyan
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
$storageArgs = "--storage.tsdb.retention.time=${retentionDays}d"

# Verifier le service
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "[ERREUR] Service '$serviceName' non trouve!" -ForegroundColor Red
    exit 1
}

Write-Host "Service trouve: $($service.DisplayName)" -ForegroundColor Green
Write-Host "Statut actuel: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Verifier que les fichiers existent
if (-not (Test-Path $prometheusExe)) {
    Write-Host "[ERREUR] Fichier non trouve: $prometheusExe" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Fichier trouve: $prometheusExe" -ForegroundColor Green

if (-not (Test-Path $configPath)) {
    Write-Host "[ERREUR] Configuration non trouvee: $configPath" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Configuration trouvee: $configPath" -ForegroundColor Green

# Creer le repertoire data s'il n'existe pas
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "[OK] Repertoire data cree: $dataDir" -ForegroundColor Green
}

Write-Host ""

# Tester l'execution manuelle
Write-Host "[INFO] Test d'execution manuelle de Prometheus..." -ForegroundColor Yellow
Write-Host "  Commande: `"$prometheusExe`" --config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" $storageArgs --web.listen-address=0.0.0.0:$port" -ForegroundColor Gray

try {
    $testProcess = Start-Process -FilePath $prometheusExe -ArgumentList @(
        "--config.file=$configPath",
        "--storage.tsdb.path=$dataDir",
        $storageArgs,
        "--web.listen-address=0.0.0.0:$port"
    ) -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\prometheus-test-output.txt" -RedirectStandardError "$env:TEMP\prometheus-test-error.txt"
    
    Start-Sleep -Seconds 3
    
    if ($testProcess.HasExited) {
        Write-Host "  [ERREUR] Le processus s'est arrete (code: $($testProcess.ExitCode))" -ForegroundColor Red
        if (Test-Path "$env:TEMP\prometheus-test-error.txt") {
            $errorOutput = Get-Content "$env:TEMP\prometheus-test-error.txt" -Raw
            Write-Host "  Erreurs:" -ForegroundColor Yellow
            Write-Host $errorOutput -ForegroundColor Red
        }
        if (Test-Path "$env:TEMP\prometheus-test-output.txt") {
            $stdOutput = Get-Content "$env:TEMP\prometheus-test-output.txt" -Raw
            Write-Host "  Sortie:" -ForegroundColor Yellow
            Write-Host $stdOutput -ForegroundColor Gray
        }
        Stop-Process -Id $testProcess.Id -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  [OK] Le processus fonctionne en mode test" -ForegroundColor Green
        Stop-Process -Id $testProcess.Id -Force
        Start-Sleep -Seconds 1
    }
    
    # Nettoyer les fichiers temporaires
    Remove-Item "$env:TEMP\prometheus-test-output.txt" -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:TEMP\prometheus-test-error.txt" -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "  [ERREUR] Impossible d'executer: $_" -ForegroundColor Red
    Write-Host "  Exception: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Verifier la configuration actuelle du service
Write-Host "[INFO] Configuration actuelle du service..." -ForegroundColor Yellow
$serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
if ($serviceWmi) {
    Write-Host "  Chemin: $($serviceWmi.PathName)" -ForegroundColor White
    Write-Host "  Type de demarrage: $($serviceWmi.StartMode)" -ForegroundColor White
    Write-Host "  Etat: $($serviceWmi.State)" -ForegroundColor White
}

Write-Host ""

# Corriger le service
Write-Host "[INFO] Correction de la configuration du service..." -ForegroundColor Yellow

# Arreter le service s'il tourne
if ($service.Status -eq "Running") {
    Write-Host "  Arret du service..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Supprimer et recreer le service
Write-Host "  Suppression de l'ancien service..." -ForegroundColor Yellow
& sc.exe delete $serviceName 2>&1 | Out-Null
Start-Sleep -Seconds 2

# Construire les arguments correctement
$arguments = "--config.file=`"$configPath`" --storage.tsdb.path=`"$dataDir`" $storageArgs --web.listen-address=0.0.0.0:$port"
$binPath = "`"$prometheusExe`" $arguments"

Write-Host "  Creation du nouveau service..." -ForegroundColor Yellow
Write-Host "    binPath: $binPath" -ForegroundColor Gray

try {
    Write-Host "  Parametres du service:" -ForegroundColor Gray
    Write-Host "    Name: $serviceName" -ForegroundColor Gray
    Write-Host "    BinaryPathName: $binPath" -ForegroundColor Gray
    Write-Host "    DisplayName: Prometheus Server" -ForegroundColor Gray
    Write-Host "    StartupType: Automatic" -ForegroundColor Gray
    
    $serviceParams = @{
        Name = $serviceName
        BinaryPathName = $binPath
        DisplayName = "Prometheus Server"
        StartupType = "Automatic"
        Description = "Prometheus monitoring system and time series database"
    }
    
    Write-Host "  Creation du service..." -ForegroundColor Gray
    $newService = New-Service @serviceParams -ErrorAction Stop
    Write-Host "[OK] Service recre avec succes (ID: $($newService.Status))" -ForegroundColor Green
    
    # Attendre un peu pour que le service soit enregistre
    Start-Sleep -Seconds 2
    
    # Verifier que le service existe
    $verifyService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($verifyService) {
        Write-Host "  [OK] Service verifie: $($verifyService.DisplayName)" -ForegroundColor Green
    } else {
        Write-Host "  [ERREUR] Service non trouve apres creation!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Echec de la creation: $_" -ForegroundColor Red
    Write-Host "  Exception Type: $($_.Exception.GetType().FullName)" -ForegroundColor Red
    Write-Host "  Exception Message: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.InnerException) {
        Write-Host "  Inner Exception: $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
    Write-Host "  Stack Trace:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}

# Demarrer le service
Write-Host ""
Write-Host "[INFO] Demarrage du service..." -ForegroundColor Yellow

# Verifier l'etat avant demarrage
$serviceBefore = Get-Service -Name $serviceName
Write-Host "  Etat avant demarrage: $($serviceBefore.Status)" -ForegroundColor Gray

try {
    Write-Host "  Tentative de demarrage..." -ForegroundColor Gray
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "  [OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre et verifier plusieurs fois
    $maxWait = 10
    $waited = 0
    $serviceStarted = $false
    
    while ($waited -lt $maxWait -and -not $serviceStarted) {
        Start-Sleep -Seconds 1
        $waited++
        $currentService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($currentService -and $currentService.Status -eq "Running") {
            $serviceStarted = $true
            Write-Host "  [OK] Service demarre apres $waited secondes" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Attente... ($waited/$maxWait s) - Statut: $($currentService.Status)" -ForegroundColor Gray
        }
    }
    
    Start-Sleep -Seconds 2
    
    $service = Get-Service -Name $serviceName
    Write-Host ""
    Write-Host "  Etat final du service: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Running"){"Green"}else{"Red"})
    
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service demarre avec succes!" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Service toujours arrete. Statut: $($service.Status)" -ForegroundColor Red
        
        # Essayer de voir les details du service
        Write-Host ""
        Write-Host "  Details du service:" -ForegroundColor Yellow
        $serviceDetails = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
        if ($serviceDetails) {
            Write-Host "    Etat: $($serviceDetails.State)" -ForegroundColor White
            Write-Host "    Type de demarrage: $($serviceDetails.StartMode)" -ForegroundColor White
            Write-Host "    Compte: $($serviceDetails.StartName)" -ForegroundColor White
            Write-Host "    Chemin: $($serviceDetails.PathName)" -ForegroundColor White
            Write-Host "    Code d'erreur: $($serviceDetails.ExitCode)" -ForegroundColor $(if($serviceDetails.ExitCode -eq 0){"Green"}else{"Red"})
        }
        
        # Verifier les logs d'evenements Windows
        Write-Host ""
        Write-Host "Verification des logs d'evenements Windows..." -ForegroundColor Yellow
        
        # Logs Application
        $appEvents = Get-EventLog -LogName Application -Newest 30 -ErrorAction SilentlyContinue | Where-Object { $_.Source -match "Prometheus" -or $_.Message -match "Prometheus" -or $_.Message -match "prometheus" }
        if ($appEvents) {
            Write-Host "  Evenements Application:" -ForegroundColor Yellow
            foreach ($event in $appEvents | Select-Object -First 10) {
                $message = $event.Message
                if ($message.Length -gt 300) {
                    $message = $message.Substring(0, 300) + "..."
                }
                $color = if($event.EntryType -eq 'Error'){'Red'}elseif($event.EntryType -eq 'Warning'){'Yellow'}else{'Gray'}
                Write-Host "    [$($event.TimeGenerated)] $($event.EntryType) (ID: $($event.EventID)):" -ForegroundColor $color
                Write-Host "      $message" -ForegroundColor $color
            }
        }
        
        # Logs System
        $systemEvents = Get-EventLog -LogName System -Newest 30 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match "Prometheus" -or $_.Message -match "prometheus" }
        if ($systemEvents) {
            Write-Host "  Evenements System:" -ForegroundColor Yellow
            foreach ($event in $systemEvents | Select-Object -First 5) {
                $message = $event.Message
                if ($message.Length -gt 300) {
                    $message = $message.Substring(0, 300) + "..."
                }
                $color = if($event.EntryType -eq 'Error'){'Red'}elseif($event.EntryType -eq 'Warning'){'Yellow'}else{'Gray'}
                Write-Host "    [$($event.TimeGenerated)] $($event.EntryType) (ID: $($event.EventID)):" -ForegroundColor $color
                Write-Host "      $message" -ForegroundColor $color
            }
        }
        
        # Verifier les logs de Prometheus si disponibles
        $prometheusLogDir = Join-Path $installDir "logs"
        if (Test-Path $prometheusLogDir) {
            Write-Host ""
            Write-Host "  Logs Prometheus:" -ForegroundColor Yellow
            $logFiles = Get-ChildItem -Path $prometheusLogDir -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($logFiles) {
                $lastLog = Get-Content $logFiles.FullName -Tail 20 -ErrorAction SilentlyContinue
                if ($lastLog) {
                    Write-Host "    Dernieres lignes de $($logFiles.Name):" -ForegroundColor Gray
                    $lastLog | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
                }
            }
        }
        
        # Verifier le compte de service
        Write-Host ""
        Write-Host "  Configuration du service:" -ForegroundColor Yellow
        $serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
        if ($serviceWmi) {
            Write-Host "    Compte: $($serviceWmi.StartName)" -ForegroundColor White
            Write-Host "    Chemin: $($serviceWmi.PathName)" -ForegroundColor White
        }
        
        # Verifier si le port est utilise
        $portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($portInUse) {
            Write-Host ""
            Write-Host "  [INFO] Le port $port est utilise par un autre processus" -ForegroundColor Yellow
        }
        
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Impossible de demarrer: $_" -ForegroundColor Red
    
    # Afficher plus de details
    Write-Host ""
    Write-Host "Details de l'erreur:" -ForegroundColor Yellow
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.InnerException) {
        Write-Host "  $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
    
    exit 1
}

# Verifier que Prometheus est accessible
Write-Host ""
Write-Host "[INFO] Verification de l'acces..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:${port}" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Prometheus fonctionne correctement!" -ForegroundColor Green
        Write-Host "  Local: http://localhost:${port}" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${port}" -ForegroundColor Cyan
        
        # Verifier les targets
        Write-Host ""
        Write-Host "[INFO] Verification des targets..." -ForegroundColor Yellow
        try {
            $targetsResponse = Invoke-WebRequest -Uri "http://localhost:${port}/api/v1/targets" -UseBasicParsing -TimeoutSec 5
            $targets = $targetsResponse.Content | ConvertFrom-Json
            if ($targets.data.activeTargets) {
                foreach ($target in $targets.data.activeTargets) {
                    $status = if ($target.health -eq "up") { "[OK]" } else { "[ERREUR]" }
                    $color = if($target.health -eq "up"){"Green"}else{"Red"}
                    Write-Host "  $status $($target.labels.job): $($target.scrapeUrl) - $($target.health)" -ForegroundColor $color
                }
            }
        } catch {
            Write-Host "  [AVERTISSEMENT] Impossible de verifier les targets" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[AVERTISSEMENT] Prometheus demarre mais le port peut necessiter plus de temps" -ForegroundColor Yellow
    Write-Host "  Essayez d'acceder a http://${serverHost}:${port} dans quelques secondes" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminee!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
