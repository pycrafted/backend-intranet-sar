# =============================================================================
# Script PowerShell pour démarrer Waitress en production (Windows)
# =============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Démarrage de Waitress pour SAR Backend" -ForegroundColor Cyan
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

# Vérifier que Waitress est installé
Write-Host "Vérification de Waitress..." -ForegroundColor Yellow
$waitressCheck = & python -c "import waitress; print(waitress.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Waitress n'est pas installé" -ForegroundColor Red
    Write-Host "Installation de Waitress..." -ForegroundColor Yellow
    & pip install waitress
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Échec de l'installation de Waitress" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Waitress installé" -ForegroundColor Green
} else {
    Write-Host "[OK] Waitress version: $waitressCheck" -ForegroundColor Green
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
$port = $env:WAITRESS_PORT
if (-not $port) {
    $port = "8001"
    Write-Host "[INFO] Port non défini, utilisation du port par défaut: $port" -ForegroundColor Gray
}

$threads = $env:WAITRESS_THREADS
if (-not $threads) {
    $threads = "4"
    Write-Host "[INFO] Nombre de threads non défini, utilisation par défaut: $threads" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Host: 0.0.0.0" -ForegroundColor White
Write-Host "  Port: $port" -ForegroundColor White
Write-Host "  Threads: $threads" -ForegroundColor White
Write-Host "  Application: master.wsgi:application" -ForegroundColor White
Write-Host ""

# Démarrer Waitress
Write-Host "Démarrage de Waitress..." -ForegroundColor Yellow
Write-Host ""

# Méthode 1: Utiliser waitress-serve (recommandé)
try {
    & waitress-serve `
        --host=0.0.0.0 `
        --port=$port `
        --threads=$threads `
        --channel-timeout=120 `
        master.wsgi:application
} catch {
    Write-Host ""
    Write-Host "[ERREUR] Échec du démarrage de Waitress avec waitress-serve" -ForegroundColor Red
    Write-Host "Tentative avec Python direct..." -ForegroundColor Yellow
    Write-Host ""
    
    # Méthode alternative: Python direct
    & python -m waitress `
        --host=0.0.0.0 `
        --port=$port `
        --threads=$threads `
        --channel-timeout=120 `
        master.wsgi:application
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERREUR] Échec du démarrage de Waitress" -ForegroundColor Red
        exit 1
    }
}

