# Script pour démarrer tous les services de monitoring
# Usage: .\start-monitoring.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Démarrage des services de monitoring" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Configuration du serveur
$serverHost = "sar-intranet.sar.sn"

# Liste des services à démarrer
$services = @(
    @{Name = "windows_exporter"; DisplayName = "Windows Exporter"; Port = 9182; URL = "http://${serverHost}:9182/metrics"},
    @{Name = "Prometheus"; DisplayName = "Prometheus"; Port = 9090; URL = "http://${serverHost}:9090"},
    @{Name = "Grafana"; DisplayName = "Grafana"; Port = 3002; URL = "http://${serverHost}:3002"}
)

$allStarted = $true

foreach ($serviceInfo in $services) {
    $serviceName = $serviceInfo.Name
    $displayName = $serviceInfo.DisplayName
    $port = $serviceInfo.Port
    $url = $serviceInfo.URL
    
    Write-Host "[INFO] Vérification de $displayName..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    
    if (-not $service) {
        Write-Host "  ✗ Service '$serviceName' non trouvé" -ForegroundColor Red
        Write-Host "    Installez-le avec le script approprié" -ForegroundColor Yellow
        $allStarted = $false
        continue
    }
    
    if ($service.Status -eq "Running") {
        Write-Host "  ✓ $displayName est déjà en cours d'exécution" -ForegroundColor Green
        
        # Vérifier que le port répond
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            Write-Host "    ✓ Accessible sur $url" -ForegroundColor Green
        } catch {
            Write-Host "    ⚠ Port $port accessible mais URL peut ne pas répondre encore" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  → Démarrage de $displayName..." -ForegroundColor Yellow
        try {
            Start-Service -Name $serviceName -ErrorAction Stop
            Start-Sleep -Seconds 3
            
            $service = Get-Service -Name $serviceName
            if ($service.Status -eq "Running") {
                Write-Host "    ✓ $displayName démarré avec succès" -ForegroundColor Green
                
                # Attendre un peu puis vérifier l'URL
                Start-Sleep -Seconds 2
                try {
                    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                    Write-Host "    ✓ Accessible sur $url" -ForegroundColor Green
                } catch {
                    Write-Host "    ⚠ Service démarré mais URL peut nécessiter plus de temps" -ForegroundColor Yellow
                }
            } else {
                Write-Host "    ✗ Échec du démarrage. Statut: $($service.Status)" -ForegroundColor Red
                $allStarted = $false
            }
        } catch {
            Write-Host "    ✗ Erreur lors du démarrage: $_" -ForegroundColor Red
            $allStarted = $false
        }
    }
    
    Write-Host ""
}

# Résumé
Write-Host "=========================================" -ForegroundColor Cyan
if ($allStarted) {
    Write-Host "Tous les services sont démarrés!" -ForegroundColor Green
} else {
    Write-Host "Certains services n'ont pas démarré" -ForegroundColor Yellow
}
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$serverHost = "sar-intranet.sar.sn"
Write-Host "URLs d'accès:" -ForegroundColor Yellow
Write-Host "  Windows Exporter: http://${serverHost}:9182/metrics" -ForegroundColor Cyan
Write-Host "  Prometheus:       http://${serverHost}:9090" -ForegroundColor Cyan
Write-Host "  Grafana:          http://${serverHost}:3002" -ForegroundColor Cyan
Write-Host ""

Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  # Voir le statut de tous les services:" -ForegroundColor White
Write-Host "  Get-Service -Name windows_exporter,Prometheus,Grafana" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Redémarrer tous les services:" -ForegroundColor White
Write-Host "  Restart-Service -Name windows_exporter,Prometheus,Grafana" -ForegroundColor Cyan
Write-Host ""

