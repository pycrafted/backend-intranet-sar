# Script pour activer tous les comptes utilisateurs
# Usage: .\activate-all-users.ps1 [--dry-run]
# Exemple: .\activate-all-users.ps1
# Exemple (simulation): .\activate-all-users.ps1 --dry-run

param(
    [switch]$DryRun = $false
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = $scriptPath

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Activation de tous les comptes utilisateurs" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si on est dans le bon répertoire
if (-not (Test-Path (Join-Path $backendPath "manage.py"))) {
    Write-Host "[ERREUR] Le fichier manage.py n'a pas été trouvé!" -ForegroundColor Red
    Write-Host "Assurez-vous d'exécuter ce script depuis le répertoire backend-intranet-sar" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Répertoire backend trouvé: $backendPath" -ForegroundColor Green
Write-Host ""

# Vérifier si l'environnement virtuel existe
$venvPath = Join-Path $backendPath "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $venvActivate) {
    Write-Host "[INFO] Activation de l'environnement virtuel..." -ForegroundColor Yellow
    & $venvActivate
    Write-Host "[OK] Environnement virtuel activé" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[AVERTISSEMENT] Environnement virtuel non trouvé à: $venvPath" -ForegroundColor Yellow
    Write-Host "[INFO] Tentative d'exécution sans environnement virtuel..." -ForegroundColor Yellow
    Write-Host ""
}

# Construire la commande
$command = "python manage.py force_activate_all_users"
if ($DryRun) {
    $command += " --dry-run"
    Write-Host "[INFO] Mode DRY-RUN activé - aucune modification ne sera effectuée" -ForegroundColor Yellow
    Write-Host ""
}

# Changer vers le répertoire backend
Push-Location $backendPath

try {
    Write-Host "Exécution de la commande Django..." -ForegroundColor Cyan
    Write-Host "Commande: $command" -ForegroundColor Gray
    Write-Host ""
    
    # Exécuter la commande
    Invoke-Expression $command
    
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Opération terminée" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $DryRun) {
        Write-Host "✅ Tous les comptes utilisateurs ont été activés" -ForegroundColor Green
        Write-Host "💡 Les utilisateurs peuvent maintenant se connecter à l'application" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "[ERREUR] Une erreur s'est produite lors de l'exécution:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host ""

