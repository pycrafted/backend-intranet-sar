# =============================================================================
# Script PowerShell pour démarrer Django en mode développement (port 8002)
# =============================================================================

Write-Host "=========================================" -ForegroundColor Magenta
Write-Host "Demarrage Django DEV - SAR Backend (8002)" -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host ""

$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[ERREUR] L'environnement virtuel n'existe pas: $venvPath" -ForegroundColor Red
    exit 1
}

Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

$envDevFile = ".env.dev"
if (Test-Path $envDevFile) {
    Write-Host "Chargement des variables depuis $envDevFile..." -ForegroundColor Yellow
    Get-Content $envDevFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "[OK] Variables .env.dev chargees" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Fichier $envDevFile introuvable" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Configuration DEV:" -ForegroundColor Cyan
Write-Host "  Port: 8002" -ForegroundColor White
Write-Host "  Frontend attendu sur: http://sar-intranet.sar.sn:3000" -ForegroundColor White
Write-Host ""

& python manage.py runserver 0.0.0.0:8002
