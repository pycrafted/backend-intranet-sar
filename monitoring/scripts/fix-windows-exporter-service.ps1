# Script pour diagnostiquer et corriger le service Windows Exporter
# Usage: .\fix-windows-exporter-service.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Diagnostic et correction Windows Exporter" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    exit 1
}

$serviceName = "windows_exporter"
$exporterPath = "C:\Program Files\windows_exporter\windows_exporter.exe"
$port = 9182
# Note: 'cs' n'existe pas dans la v0.31.3, utiliser les collectors valides
$collectors = "cpu,logical_disk,memory,net,os,process,system,textfile"
$arguments = "--web.listen-address=0.0.0.0:$port --collectors.enabled=$collectors"

# Vérifier le service
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "[ERREUR] Service '$serviceName' non trouvé!" -ForegroundColor Red
    exit 1
}

Write-Host "Service trouvé: $($service.DisplayName)" -ForegroundColor Green
Write-Host "Statut actuel: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Vérifier que le fichier existe
if (-not (Test-Path $exporterPath)) {
    Write-Host "[ERREUR] Fichier non trouvé: $exporterPath" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Fichier trouvé: $exporterPath" -ForegroundColor Green
Write-Host ""

# Tester l'exécution manuelle
Write-Host "[INFO] Test d'exécution manuelle..." -ForegroundColor Yellow
Write-Host "  Commande: `"$exporterPath`" $arguments" -ForegroundColor Gray

try {
    $testProcess = Start-Process -FilePath $exporterPath -ArgumentList $arguments.Split(' ') -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    if ($testProcess.HasExited) {
        Write-Host "  [ERREUR] Le processus s'est arrêté immédiatement (code: $($testProcess.ExitCode))" -ForegroundColor Red
        Stop-Process -Id $testProcess.Id -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  [OK] Le processus fonctionne en mode test" -ForegroundColor Green
        Stop-Process -Id $testProcess.Id -Force
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "  [ERREUR] Impossible d'exécuter: $_" -ForegroundColor Red
}

Write-Host ""

# Vérifier la configuration du service
Write-Host "[INFO] Configuration actuelle du service..." -ForegroundColor Yellow
$serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
if ($serviceWmi) {
    Write-Host "  Chemin: $($serviceWmi.PathName)" -ForegroundColor White
    Write-Host "  Type de démarrage: $($serviceWmi.StartMode)" -ForegroundColor White
    Write-Host "  État: $($serviceWmi.State)" -ForegroundColor White
}

Write-Host ""

# Corriger le service
Write-Host "[INFO] Correction de la configuration du service..." -ForegroundColor Yellow

# Arrêter le service s'il tourne
if ($service.Status -eq "Running") {
    Write-Host "  Arrêt du service..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Supprimer et recréer le service avec la bonne syntaxe
Write-Host "  Suppression de l'ancien service..." -ForegroundColor Yellow
& sc.exe delete $serviceName 2>&1 | Out-Null
Start-Sleep -Seconds 2

# Créer le service avec New-Service (plus fiable)
Write-Host "  Création du nouveau service..." -ForegroundColor Yellow
try {
    $serviceParams = @{
        Name = $serviceName
        BinaryPathName = "`"$exporterPath`" $arguments"
        DisplayName = "Windows Exporter"
        StartupType = "Automatic"
        Description = "Prometheus exporter for Windows machines"
    }
    New-Service @serviceParams -ErrorAction Stop | Out-Null
    Write-Host "[OK] Service recréé avec succès" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Échec de la création: $_" -ForegroundColor Red
    exit 1
}

# Démarrer le service
Write-Host ""
Write-Host "[INFO] Démarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Start-Sleep -Seconds 3
    
    $service = Get-Service -Name $serviceName
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service démarré avec succès!" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Service toujours arrêté. Statut: $($service.Status)" -ForegroundColor Red
        
        # Vérifier les logs
        $events = Get-EventLog -LogName Application -Newest 10 -ErrorAction SilentlyContinue | Where-Object { $_.Source -match "windows_exporter" -or $_.Message -match "windows_exporter" }
        if ($events) {
            Write-Host ""
            Write-Host "Événements récents:" -ForegroundColor Yellow
            foreach ($event in $events | Select-Object -First 3) {
                Write-Host "  [$($event.TimeGenerated)] $($event.EntryType): $($event.Message.Substring(0, [Math]::Min(150, $event.Message.Length)))..." -ForegroundColor $(if($event.EntryType -eq 'Error'){'Red'}else{'Yellow'})
            }
        }
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Impossible de démarrer: $_" -ForegroundColor Red
    exit 1
}

# Vérifier que le port répond
Write-Host ""
Write-Host "[INFO] Vérification de l'accès..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:${port}/metrics" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Windows Exporter fonctionne correctement!" -ForegroundColor Green
        Write-Host "  Local: http://localhost:${port}/metrics" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${port}/metrics" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[AVERTISSEMENT] Le service démarre mais le port peut nécessiter plus de temps" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

