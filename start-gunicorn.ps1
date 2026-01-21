# =============================================================================
# Script PowerShell pour démarrer Gunicorn en production
# =============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Démarrage de Gunicorn pour SAR Backend" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que l'environnement virtuel existe
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[ERREUR] L'environnement virtuel n'existe pas: $venvPath" -ForegroundColor Red
    Write-Host "Créez-le avec: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Vérifier que Gunicorn est installé
Write-Host "Vérification de Gunicorn..." -ForegroundColor Yellow
$gunicornCheck = & python -c "import gunicorn; print(gunicorn.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Gunicorn n'est pas installé" -ForegroundColor Red
    Write-Host "Installez-le avec: pip install gunicorn" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "[OK] Gunicorn version: $gunicornCheck" -ForegroundColor Green
}

# Charger les variables d'environnement depuis .env si présent
if (Test-Path ".env") {
    Write-Host "Chargement des variables d'environnement depuis .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Configuration par défaut
$port = $env:GUNICORN_PORT
if (-not $port) {
    $port = "8001"
    Write-Host "[INFO] Port non défini, utilisation du port par défaut: $port" -ForegroundColor Gray
}

$workers = $env:GUNICORN_WORKERS
if (-not $workers) {
    $cpuCount = (Get-WmiObject Win32_ComputerSystem).NumberOfLogicalProcessors
    $workers = $cpuCount * 2 + 1
    Write-Host "[INFO] Nombre de workers non défini, calcul automatique: $workers" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Port: $port" -ForegroundColor White
Write-Host "  Workers: $workers" -ForegroundColor White
Write-Host "  Application: master.wsgi:application" -ForegroundColor White
Write-Host ""

# Vérifier que le fichier de configuration existe
$configFile = "gunicorn_config.py"
if (-not (Test-Path $configFile)) {
    Write-Host "[ATTENTION] Fichier de configuration $configFile introuvable" -ForegroundColor Yellow
    Write-Host "Démarrage avec les paramètres par défaut..." -ForegroundColor Yellow
    $configFile = $null
}

# Démarrer Gunicorn
Write-Host "Démarrage de Gunicorn..." -ForegroundColor Yellow
Write-Host ""

if ($configFile) {
    & gunicorn master.wsgi:application --config $configFile
} else {
    & gunicorn master.wsgi:application `
        --bind "0.0.0.0:$port" `
        --workers $workers `
        --timeout 120 `
        --access-logfile - `
        --error-logfile - `
        --log-level info `
        --name sar-backend
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERREUR] Échec du démarrage de Gunicorn" -ForegroundColor Red
    exit 1
}



