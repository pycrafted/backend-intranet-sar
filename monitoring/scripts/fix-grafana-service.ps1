# Script pour diagnostiquer et corriger le service Grafana
# Usage: .\fix-grafana-service.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Diagnostic et correction Grafana" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si le script est execute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Red
    exit 1
}

$serviceName = "Grafana"
$nssmExe = "C:\nssm\win64\nssm.exe"
$grafanaExe = "C:\Program Files\GrafanaLabs\grafana\bin\grafana-server.exe"
$configPath = "C:\ProgramData\GrafanaLabs\grafana\grafana.ini"
$installDir = "C:\Program Files\GrafanaLabs\grafana"
$logDir = "C:\ProgramData\GrafanaLabs\grafana\logs"

# Verifier le service
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "[ERREUR] Service '$serviceName' non trouve!" -ForegroundColor Red
    exit 1
}

Write-Host "Service trouve: $($service.DisplayName)" -ForegroundColor Green
Write-Host "Statut actuel: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Verifier les fichiers
if (-not (Test-Path $grafanaExe)) {
    Write-Host "[ERREUR] Fichier non trouve: $grafanaExe" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Fichier trouve: $grafanaExe" -ForegroundColor Green

if (-not (Test-Path $nssmExe)) {
    Write-Host "[ERREUR] NSSM non trouve: $nssmExe" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] NSSM trouve: $nssmExe" -ForegroundColor Green

if (-not (Test-Path $configPath)) {
    Write-Host "[ERREUR] Configuration non trouvee: $configPath" -ForegroundColor Red
    Write-Host "  Le fichier grafana.ini doit exister" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Configuration trouvee: $configPath" -ForegroundColor Green

# Verifier le contenu de la configuration
Write-Host "[INFO] Verification de la configuration..." -ForegroundColor Yellow
$configContent = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
if ($configContent -match "http_port\s*=\s*3002") {
    Write-Host "  [OK] Port 3002 configure" -ForegroundColor Green
} else {
    Write-Host "  [AVERTISSEMENT] Port 3002 non trouve dans la configuration" -ForegroundColor Yellow
}

Write-Host ""

# Arreter le service forcement
Write-Host "[INFO] Arret force du service..." -ForegroundColor Yellow
try {
    Stop-Service -Name $serviceName -Force -ErrorAction Stop
    Start-Sleep -Seconds 3
    Write-Host "[OK] Service arrete" -ForegroundColor Green
} catch {
    Write-Host "[AVERTISSEMENT] Impossible d'arreter le service: $_" -ForegroundColor Yellow
}

# Supprimer le service
Write-Host "[INFO] Suppression du service..." -ForegroundColor Yellow
& $nssmExe remove $serviceName confirm 2>&1 | Out-Null
& sc.exe delete $serviceName 2>&1 | Out-Null
Start-Sleep -Seconds 2

# Verifier que le service est supprime
$checkService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($checkService) {
    Write-Host "[ERREUR] Le service existe toujours. Tentative de suppression forcee..." -ForegroundColor Red
    # Essayer avec sc.exe delete force
    & sc.exe delete $serviceName 2>&1 | Out-Null
    Start-Sleep -Seconds 3
} else {
    Write-Host "[OK] Service supprime" -ForegroundColor Green
}

Write-Host ""

# Recréer le service avec NSSM
Write-Host "[INFO] Recreation du service avec NSSM..." -ForegroundColor Yellow

# Installer le service
Write-Host "  Installation..." -ForegroundColor Gray
$installResult = & $nssmExe install $serviceName $grafanaExe 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Echec de l'installation: $installResult" -ForegroundColor Red
    exit 1
}

# Configurer les arguments (sans guillemets dans les chemins pour NSSM)
Write-Host "  Configuration des arguments..." -ForegroundColor Gray
$nssmArgs = "--config=$configPath --homepath=$installDir"
& $nssmExe set $serviceName AppParameters $nssmArgs 2>&1 | Out-Null

# Configurer les autres parametres
Write-Host "  Configuration des autres parametres..." -ForegroundColor Gray
& $nssmExe set $serviceName DisplayName "Grafana" 2>&1 | Out-Null
& $nssmExe set $serviceName Description "Grafana - The open observability platform" 2>&1 | Out-Null
& $nssmExe set $serviceName Start SERVICE_AUTO_START 2>&1 | Out-Null
& $nssmExe set $serviceName AppDirectory $installDir 2>&1 | Out-Null

# Configurer les logs
& $nssmExe set $serviceName AppStdout (Join-Path $logDir "grafana-stdout.log") 2>&1 | Out-Null
& $nssmExe set $serviceName AppStderr (Join-Path $logDir "grafana-stderr.log") 2>&1 | Out-Null

# Desactiver la pause (si c'etait le probleme)
& $nssmExe set $serviceName AppStopMethodSkip 1 2>&1 | Out-Null

Write-Host "[OK] Service recree" -ForegroundColor Green
Write-Host ""

# Verifier la configuration NSSM avant demarrage
Write-Host "[INFO] Verification de la configuration NSSM..." -ForegroundColor Yellow
$nssmApp = & $nssmExe get $serviceName AppApplication 2>&1
$nssmParams = & $nssmExe get $serviceName AppParameters 2>&1
$nssmDir = & $nssmExe get $serviceName AppDirectory 2>&1

Write-Host "  Application: $nssmApp" -ForegroundColor Gray
Write-Host "  Parameters: $nssmParams" -ForegroundColor Gray
Write-Host "  Directory: $nssmDir" -ForegroundColor Gray
Write-Host ""

# Tester l'execution manuelle
Write-Host "[INFO] Test d'execution manuelle de Grafana..." -ForegroundColor Yellow
Write-Host "  Commande: `"$grafanaExe`" --config=`"$configPath`" --homepath=`"$installDir`"" -ForegroundColor Gray

try {
    # Separer les arguments correctement
    $argList = @(
        "--config=$configPath",
        "--homepath=$installDir"
    )
    
    Write-Host "  Arguments separes: $($argList -join ' ')" -ForegroundColor Gray
    
    $testProcess = Start-Process -FilePath $grafanaExe -ArgumentList $argList -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\grafana-test-output.txt" -RedirectStandardError "$env:TEMP\grafana-test-error.txt" -WorkingDirectory $installDir
    
    Start-Sleep -Seconds 5
    
    if ($testProcess.HasExited) {
        Write-Host "  [ERREUR] Le processus s'est arrete (code: $($testProcess.ExitCode))" -ForegroundColor Red
        if (Test-Path "$env:TEMP\grafana-test-error.txt") {
            $errorOutput = Get-Content "$env:TEMP\grafana-test-error.txt" -Raw -ErrorAction SilentlyContinue
            Write-Host "  Erreurs:" -ForegroundColor Yellow
            Write-Host $errorOutput -ForegroundColor Red
        }
        if (Test-Path "$env:TEMP\grafana-test-output.txt") {
            $stdOutput = Get-Content "$env:TEMP\grafana-test-output.txt" -Raw -ErrorAction SilentlyContinue
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
    Remove-Item "$env:TEMP\grafana-test-output.txt" -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:TEMP\grafana-test-error.txt" -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "  [ERREUR] Impossible d'executer: $_" -ForegroundColor Red
    Write-Host "  Exception: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Demarrer le service
Write-Host "[INFO] Demarrage du service..." -ForegroundColor Yellow

# Verifier l'etat avant demarrage
$serviceBefore = Get-Service -Name $serviceName
Write-Host "  Etat avant demarrage: $($serviceBefore.Status)" -ForegroundColor Gray

try {
    Write-Host "  Tentative de demarrage..." -ForegroundColor Gray
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "  [OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre et verifier plusieurs fois
    $maxWait = 30
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
            if ($waited % 5 -eq 0) {
                Write-Host "  [INFO] Attente... ($waited/$maxWait s) - Statut: $($currentService.Status)" -ForegroundColor Gray
            }
        }
    }
    
    Start-Sleep -Seconds 2
    
    $finalService = Get-Service -Name $serviceName
    Write-Host ""
    Write-Host "  Etat final du service: $($finalService.Status)" -ForegroundColor $(if($finalService.Status -eq "Running"){"Green"}else{"Red"})
    
    if ($finalService.Status -eq "Running") {
        Write-Host ""
        Write-Host "[OK] Grafana fonctionne!" -ForegroundColor Green
        Write-Host "  Local: http://localhost:3002" -ForegroundColor Cyan
        Write-Host "  Serveur: http://sar-intranet.sar.sn:3002" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERREUR] Service toujours arrete. Statut: $($finalService.Status)" -ForegroundColor Red
        
        # Afficher les details du service
        Write-Host ""
        Write-Host "Details du service:" -ForegroundColor Yellow
        $serviceDetails = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
        if ($serviceDetails) {
            Write-Host "  Etat: $($serviceDetails.State)" -ForegroundColor White
            Write-Host "  Type de demarrage: $($serviceDetails.StartMode)" -ForegroundColor White
            Write-Host "  Compte: $($serviceDetails.StartName)" -ForegroundColor White
            Write-Host "  Chemin: $($serviceDetails.PathName)" -ForegroundColor White
            Write-Host "  Code d'erreur: $($serviceDetails.ExitCode)" -ForegroundColor $(if($serviceDetails.ExitCode -eq 0){"Green"}else{"Red"})
        }
        
        # Verifier les logs d'evenements Windows
        Write-Host ""
        Write-Host "Verification des logs d'evenements Windows..." -ForegroundColor Yellow
        $systemEvents = Get-EventLog -LogName System -Newest 20 -ErrorAction SilentlyContinue | Where-Object { $_.Source -eq "Service Control Manager" -or $_.Message -match "Grafana" }
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
        
        # Afficher les logs NSSM
        Write-Host ""
        Write-Host "Logs NSSM:" -ForegroundColor Yellow
        if (Test-Path (Join-Path $logDir "grafana-stderr.log")) {
            Write-Host "  Dernieres erreurs (stderr.log):" -ForegroundColor Yellow
            $stderrContent = Get-Content (Join-Path $logDir "grafana-stderr.log") -Tail 20 -ErrorAction SilentlyContinue
            if ($stderrContent) {
                $stderrContent | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
            } else {
                Write-Host "    (fichier vide)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  Fichier stderr.log non trouve" -ForegroundColor Gray
        }
        
        if (Test-Path (Join-Path $logDir "grafana-stdout.log")) {
            Write-Host "  Dernieres sorties (stdout.log):" -ForegroundColor Yellow
            $stdoutContent = Get-Content (Join-Path $logDir "grafana-stdout.log") -Tail 20 -ErrorAction SilentlyContinue
            if ($stdoutContent) {
                $stdoutContent | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
            } else {
                Write-Host "    (fichier vide)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  Fichier stdout.log non trouve" -ForegroundColor Gray
        }
        
        # Verifier les logs Grafana standards
        $grafanaLogFiles = Get-ChildItem -Path $logDir -Filter "grafana.log" -ErrorAction SilentlyContinue
        if ($grafanaLogFiles) {
            Write-Host ""
            Write-Host "  Logs Grafana standards:" -ForegroundColor Yellow
            foreach ($logFile in $grafanaLogFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1) {
                $logContent = Get-Content $logFile.FullName -Tail 20 -ErrorAction SilentlyContinue
                if ($logContent) {
                    Write-Host "    Dernieres lignes de $($logFile.Name):" -ForegroundColor Gray
                    $logContent | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
                }
            }
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
    Write-Host "  Stack Trace:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminee!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

