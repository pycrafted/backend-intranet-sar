# Script maître pour installer tous les composants de monitoring
# Installe Windows Exporter, Prometheus et Grafana dans l'ordre
# Usage: .\install-all.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation complète du monitoring" -ForegroundColor Cyan
Write-Host "Intranet SAR - Windows Server 2022" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Obtenir le répertoire du script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Ce script va installer:" -ForegroundColor Yellow
Write-Host "  1. Windows Exporter (métriques système)" -ForegroundColor White
Write-Host "  2. Prometheus (collecte et stockage)" -ForegroundColor White
Write-Host "  3. Grafana (visualisation)" -ForegroundColor White
Write-Host ""
Write-Host "Temps estimé: 15-20 minutes" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Voulez-vous continuer? (O/N)"
if ($confirm -ne 'O' -and $confirm -ne 'o') {
    Write-Host "[ANNULÉ] Installation annulée" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Étape 1/3 : Installation de Windows Exporter" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$windowsExporterScript = Join-Path $scriptDir "install-windows-exporter.ps1"
if (Test-Path $windowsExporterScript) {
    & $windowsExporterScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Échec de l'installation de Windows Exporter" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERREUR] Script install-windows-exporter.ps1 non trouvé!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Étape 2/3 : Installation de Prometheus" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$prometheusScript = Join-Path $scriptDir "install-prometheus.ps1"
if (Test-Path $prometheusScript) {
    & $prometheusScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Échec de l'installation de Prometheus" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERREUR] Script install-prometheus.ps1 non trouvé!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Étape 3/3 : Installation de Grafana" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$grafanaScript = Join-Path $scriptDir "install-grafana.ps1"
if (Test-Path $grafanaScript) {
    & $grafanaScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Échec de l'installation de Grafana" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERREUR] Script install-grafana.ps1 non trouvé!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Vérification finale" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que tous les services sont démarrés
$allServicesRunning = $true

$services = @(
    @{Name = "windows_exporter"; DisplayName = "Windows Exporter"},
    @{Name = "Prometheus"; DisplayName = "Prometheus"},
    @{Name = "Grafana"; DisplayName = "Grafana"}
)

foreach ($serviceInfo in $services) {
    $service = Get-Service -Name $serviceInfo.Name -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-Host "  ✓ $($serviceInfo.DisplayName) : En cours d'exécution" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($serviceInfo.DisplayName) : Non démarré" -ForegroundColor Red
        $allServicesRunning = $false
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if ($allServicesRunning) {
    Write-Host "✅ Tous les services sont installés et démarrés!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Certains services ne sont pas démarrés" -ForegroundColor Yellow
    Write-Host "   Utilisez: .\start-monitoring.ps1 pour démarrer tous les services" -ForegroundColor Yellow
}

$serverHost = "sar-intranet.sar.sn"
Write-Host ""
Write-Host "URLs d'accès:" -ForegroundColor Yellow
Write-Host "  Windows Exporter: http://${serverHost}:9182/metrics" -ForegroundColor Cyan
Write-Host "  Prometheus:       http://${serverHost}:9090" -ForegroundColor Cyan
Write-Host "  Grafana:          http://${serverHost}:3002" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Accédez à Grafana: http://${serverHost}:3002" -ForegroundColor White
Write-Host "  2. Connectez-vous avec admin/admin" -ForegroundColor White
Write-Host "  3. Changez le mot de passe" -ForegroundColor White
Write-Host "  4. Ajoutez Prometheus comme source de données:" -ForegroundColor White
Write-Host "     Configuration > Data Sources > Add data source > Prometheus" -ForegroundColor Cyan
Write-Host "     URL: http://${serverHost}:9090" -ForegroundColor Cyan
Write-Host "  5. Créez vos dashboards pour monitorer CPU, RAM et Disque" -ForegroundColor White
Write-Host ""
Write-Host "Documentation complète: ..\README.md" -ForegroundColor Gray
Write-Host ""

