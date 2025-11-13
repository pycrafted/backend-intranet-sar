# Script de diagnostic et correction complet pour Grafana
# Usage: .\diagnose-grafana.ps1

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
$dataDir = "C:\ProgramData\GrafanaLabs\grafana\data"
$logDir = "C:\ProgramData\GrafanaLabs\grafana\logs"
$serverHost = "sar-intranet.sar.sn"

# 1. Verifier les fichiers
Write-Host "[1/8] Verification des fichiers..." -ForegroundColor Yellow
if (-not (Test-Path $grafanaExe)) {
    Write-Host "  [ERREUR] Grafana non trouve: $grafanaExe" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Grafana trouve: $grafanaExe" -ForegroundColor Green

if (-not (Test-Path $nssmExe)) {
    Write-Host "  [ERREUR] NSSM non trouve: $nssmExe" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] NSSM trouve: $nssmExe" -ForegroundColor Green

# 2. Creer les repertoires manquants
Write-Host ""
Write-Host "[2/8] Creation des repertoires..." -ForegroundColor Yellow
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "  [OK] Repertoire data cree: $dataDir" -ForegroundColor Green
} else {
    Write-Host "  [OK] Repertoire data existe: $dataDir" -ForegroundColor Green
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "  [OK] Repertoire logs cree: $logDir" -ForegroundColor Green
} else {
    Write-Host "  [OK] Repertoire logs existe: $logDir" -ForegroundColor Green
}

# 3. Verifier et corriger la configuration
Write-Host ""
Write-Host "[3/8] Verification de la configuration..." -ForegroundColor Yellow
if (-not (Test-Path $configPath)) {
    Write-Host "  [ERREUR] Configuration non trouvee: $configPath" -ForegroundColor Red
    exit 1
}

$content = Get-Content $configPath -Raw
$needsUpdate = $false

if ($content -notmatch "http_addr\s*=\s*0\.0\.0\.0") {
    $content = $content -replace 'http_addr\s*=', 'http_addr = 0.0.0.0'
    $needsUpdate = $true
    Write-Host "  [OK] http_addr configure a 0.0.0.0" -ForegroundColor Green
}

if ($content -notmatch "root_url\s*=\s*http://sar-intranet\.sar\.sn:3002/") {
    $content = $content -replace 'root_url\s*=.*', "root_url = http://${serverHost}:3002/"
    $needsUpdate = $true
    Write-Host "  [OK] root_url configure a http://${serverHost}:3002/" -ForegroundColor Green
}

if ($needsUpdate) {
    $content | Set-Content $configPath -NoNewline
    Write-Host "  [OK] Configuration mise a jour" -ForegroundColor Green
} else {
    Write-Host "  [OK] Configuration deja correcte" -ForegroundColor Green
}

# 4. Tester l'execution manuelle
Write-Host ""
Write-Host "[4/8] Test d'execution manuelle de Grafana..." -ForegroundColor Yellow
Write-Host "  Commande: `"$grafanaExe`" --config=`"$configPath`"" -ForegroundColor Gray

$testProcess = $null
$testOutFile = "$env:TEMP\grafana-test-out.txt"
$testErrFile = "$env:TEMP\grafana-test-err.txt"

# Nettoyer les anciens fichiers
Remove-Item $testOutFile -Force -ErrorAction SilentlyContinue
Remove-Item $testErrFile -Force -ErrorAction SilentlyContinue

try {
    Push-Location (Split-Path $grafanaExe -Parent)
    
    # Creer les fichiers de sortie vides
    New-Item -ItemType File -Path $testOutFile -Force | Out-Null
    New-Item -ItemType File -Path $testErrFile -Force | Out-Null
    
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $grafanaExe
    $psi.Arguments = "--config=`"$configPath`""
    $psi.WorkingDirectory = (Split-Path $grafanaExe -Parent)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    
    Write-Host "  Demarrage du processus..." -ForegroundColor Gray
    $process.Start() | Out-Null
    
    # Lire les sorties en temps reel
    $outputBuilder = New-Object System.Text.StringBuilder
    $errorBuilder = New-Object System.Text.StringBuilder
    
    $outputEvent = Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action {
        if ($EventArgs.Data) {
            [void]$Event.MessageData.AppendLine($EventArgs.Data)
        }
    } -MessageData $outputBuilder
    
    $errorEvent = Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action {
        if ($EventArgs.Data) {
            [void]$Event.MessageData.AppendLine($EventArgs.Data)
        }
    } -MessageData $errorBuilder
    
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    
    # Attendre jusqu'a 10 secondes
    $waited = 0
    $maxWait = 10
    while (-not $process.HasExited -and $waited -lt $maxWait) {
        Start-Sleep -Milliseconds 500
        $waited += 0.5
    }
    
    if ($process.HasExited) {
        Write-Host "  [ERREUR] Le processus s'est arrete (code: $($process.ExitCode))" -ForegroundColor Red
        
        # Attendre un peu pour que les evenements se terminent
        Start-Sleep -Seconds 1
        
        $output = $outputBuilder.ToString()
        $errors = $errorBuilder.ToString()
        
        if ($errors) {
            Write-Host "  Erreurs:" -ForegroundColor Yellow
            Write-Host $errors -ForegroundColor Red
        } else {
            Write-Host "  [INFO] Aucune erreur capturee dans stderr" -ForegroundColor Yellow
        }
        
        if ($output) {
            Write-Host "  Sortie:" -ForegroundColor Yellow
            Write-Host $output -ForegroundColor Gray
        } else {
            Write-Host "  [INFO] Aucune sortie capturee" -ForegroundColor Yellow
        }
        
        # Verifier aussi les fichiers
        if (Test-Path $testErrFile) {
            $fileErrors = Get-Content $testErrFile -Raw -ErrorAction SilentlyContinue
            if ($fileErrors -and $fileErrors.Trim()) {
                Write-Host "  Erreurs dans le fichier:" -ForegroundColor Yellow
                Write-Host $fileErrors -ForegroundColor Red
            }
        }
        
        if (Test-Path $testOutFile) {
            $fileOutput = Get-Content $testOutFile -Raw -ErrorAction SilentlyContinue
            if ($fileOutput -and $fileOutput.Trim()) {
                Write-Host "  Sortie dans le fichier:" -ForegroundColor Yellow
                Write-Host $fileOutput -ForegroundColor Gray
            }
        }
        
        # Verifier les logs Grafana standards
        Write-Host "  Verification des logs Grafana..." -ForegroundColor Yellow
        $grafanaLogFiles = Get-ChildItem -Path $logDir -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
        if ($grafanaLogFiles) {
            foreach ($logFile in $grafanaLogFiles | Select-Object -First 3) {
                $logContent = Get-Content $logFile.FullName -Tail 30 -ErrorAction SilentlyContinue
                if ($logContent) {
                    Write-Host "    Dernieres lignes de $($logFile.Name):" -ForegroundColor Gray
                    $logContent | ForEach-Object { Write-Host "      $_" -ForegroundColor $(if($_ -match "error|ERROR|fail|FAIL"){"Red"}else{"Gray"}) }
                }
            }
        } else {
            Write-Host "    Aucun fichier de log trouve dans $logDir" -ForegroundColor Yellow
        }
        
        # Verifier la base de donnees
        Write-Host "  Verification de la base de donnees..." -ForegroundColor Yellow
        $dbFile = Join-Path $dataDir "grafana.db"
        if (Test-Path $dbFile) {
            Write-Host "    Base de donnees trouvee: $dbFile" -ForegroundColor Gray
            $dbInfo = Get-Item $dbFile
            Write-Host "    Taille: $([math]::Round($dbInfo.Length/1KB, 2)) KB" -ForegroundColor Gray
            Write-Host "    Derniere modification: $($dbInfo.LastWriteTime)" -ForegroundColor Gray
        } else {
            Write-Host "    Base de donnees non trouvee (sera creee au premier demarrage)" -ForegroundColor Gray
        }
        
        # Verifier les permissions
        Write-Host "  Verification des permissions..." -ForegroundColor Yellow
        try {
            $dataAcl = Get-Acl $dataDir
            Write-Host "    Repertoire data: OK" -ForegroundColor Gray
        } catch {
            Write-Host "    [ERREUR] Probleme de permissions sur data: $_" -ForegroundColor Red
        }
        
        try {
            $logAcl = Get-Acl $logDir
            Write-Host "    Repertoire logs: OK" -ForegroundColor Gray
        } catch {
            Write-Host "    [ERREUR] Probleme de permissions sur logs: $_" -ForegroundColor Red
        }
        
        # Tester sans configuration
        Write-Host ""
        Write-Host "  Test sans configuration (valeurs par defaut)..." -ForegroundColor Yellow
        try {
            $testProcess2 = Start-Process -FilePath $grafanaExe -ArgumentList "" -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\grafana-test2-out.txt" -RedirectStandardError "$env:TEMP\grafana-test2-err.txt"
            Start-Sleep -Seconds 3
            if ($testProcess2.HasExited) {
                Write-Host "    [ERREUR] S'arrete aussi sans config (code: $($testProcess2.ExitCode))" -ForegroundColor Red
                if (Test-Path "$env:TEMP\grafana-test2-err.txt") {
                    $err2 = Get-Content "$env:TEMP\grafana-test2-err.txt" -Raw
                    if ($err2) { Write-Host "    Erreurs: $err2" -ForegroundColor Red }
                }
            } else {
                Write-Host "    [OK] Fonctionne sans configuration!" -ForegroundColor Green
                Stop-Process -Id $testProcess2.Id -Force
            }
            Remove-Item "$env:TEMP\grafana-test2-out.txt" -Force -ErrorAction SilentlyContinue
            Remove-Item "$env:TEMP\grafana-test2-err.txt" -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "    [ERREUR] Exception: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  [OK] Le processus fonctionne en mode test" -ForegroundColor Green
        Stop-Process -Id $process.Id -Force
        Start-Sleep -Seconds 1
    }
    
    # Nettoyer les evenements
    Unregister-Event -SourceIdentifier $outputEvent.Name -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier $errorEvent.Name -ErrorAction SilentlyContinue
    
    Pop-Location
} catch {
    Write-Host "  [ERREUR] Exception: $_" -ForegroundColor Red
    Write-Host "  Stack: $($_.ScriptStackTrace)" -ForegroundColor Gray
    Pop-Location
} finally {
    if ($testProcess -and -not $testProcess.HasExited) {
        Stop-Process -Id $testProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $testOutFile -Force -ErrorAction SilentlyContinue
    Remove-Item $testErrFile -Force -ErrorAction SilentlyContinue
}

# 5. Arreter et supprimer le service existant
Write-Host ""
Write-Host "[5/8] Nettoyage du service existant..." -ForegroundColor Yellow
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

& $nssmExe remove $serviceName confirm 2>&1 | Out-Null
& sc.exe delete $serviceName 2>&1 | Out-Null
Start-Sleep -Seconds 2
Write-Host "  [OK] Service supprime" -ForegroundColor Green

# 6. Creer le service avec NSSM
Write-Host ""
Write-Host "[6/8] Creation du service avec NSSM..." -ForegroundColor Yellow
$installResult = & $nssmExe install $serviceName $grafanaExe 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERREUR] Echec de l'installation: $installResult" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Service installe" -ForegroundColor Green

# Configurer les parametres
Write-Host "  Configuration des parametres..." -ForegroundColor Gray
& $nssmExe set $serviceName AppParameters "--config=$configPath" 2>&1 | Out-Null
& $nssmExe set $serviceName AppDirectory $installDir 2>&1 | Out-Null
& $nssmExe set $serviceName DisplayName "Grafana" 2>&1 | Out-Null
& $nssmExe set $serviceName Description "Grafana - The open observability platform" 2>&1 | Out-Null
& $nssmExe set $serviceName Start SERVICE_AUTO_START 2>&1 | Out-Null
& $nssmExe set $serviceName AppStdout (Join-Path $logDir "grafana-stdout.log") 2>&1 | Out-Null
& $nssmExe set $serviceName AppStderr (Join-Path $logDir "grafana-stderr.log") 2>&1 | Out-Null
Write-Host "  [OK] Parametres configures" -ForegroundColor Green

# 7. Demarrer le service
Write-Host ""
Write-Host "[7/8] Demarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "  [OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre et verifier
    $maxWait = 30
    for ($i = 1; $i -le $maxWait; $i++) {
        Start-Sleep -Seconds 1
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Write-Host "  [OK] Service demarre apres $i secondes!" -ForegroundColor Green
            break
        }
        if ($i % 5 -eq 0) {
            Write-Host "    Attente... ($i/$maxWait s) - Statut: $($service.Status)" -ForegroundColor Gray
        }
    }
    
    $finalService = Get-Service -Name $serviceName
    if ($finalService.Status -ne "Running") {
        Write-Host "  [ERREUR] Service toujours arrete. Statut: $($finalService.Status)" -ForegroundColor Red
        
        # Afficher les logs
        Write-Host ""
        Write-Host "  Logs stderr:" -ForegroundColor Yellow
        if (Test-Path (Join-Path $logDir "grafana-stderr.log")) {
            Get-Content (Join-Path $logDir "grafana-stderr.log") -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        }
        
        Write-Host "  Logs stdout:" -ForegroundColor Yellow
        if (Test-Path (Join-Path $logDir "grafana-stdout.log")) {
            Get-Content (Join-Path $logDir "grafana-stdout.log") -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        }
        
        exit 1
    }
} catch {
    Write-Host "  [ERREUR] Impossible de demarrer: $_" -ForegroundColor Red
    exit 1
}

# 8. Verifier l'acces
Write-Host ""
Write-Host "[8/8] Verification de l'acces..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://${serverHost}:3002" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] Grafana accessible!" -ForegroundColor Green
        Write-Host "  URL: http://${serverHost}:3002" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [AVERTISSEMENT] Impossible d'acceder a http://${serverHost}:3002" -ForegroundColor Yellow
    Write-Host "    Le service peut avoir besoin de plus de temps" -ForegroundColor Yellow
    Write-Host "    Verifiez le port: Get-NetTCPConnection -LocalPort 3002" -ForegroundColor Yellow
}

# Verifier le port
$portCheck = Get-NetTCPConnection -LocalPort 3002 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "  [OK] Port 3002 en ecoute" -ForegroundColor Green
} else {
    Write-Host "  [AVERTISSEMENT] Port 3002 non en ecoute" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Diagnostic termine!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Acces Grafana:" -ForegroundColor Yellow
Write-Host "  URL: http://${serverHost}:3002" -ForegroundColor Cyan
Write-Host "  Utilisateur: admin" -ForegroundColor Cyan
Write-Host "  Mot de passe: admin (changez-le a la premiere connexion)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  Get-Service -Name Grafana" -ForegroundColor White
Write-Host "  Restart-Service -Name Grafana" -ForegroundColor White
Write-Host "  Get-Content `"$logDir\grafana-stdout.log`" -Tail 20" -ForegroundColor White
Write-Host ""

