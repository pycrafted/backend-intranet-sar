# Script PowerShell pour installer toutes les dépendances Python
# Usage: .\install-dependencies.ps1

Write-Host "📦 Installation des dépendances Python..." -ForegroundColor Yellow

# Vérifier que l'environnement virtuel existe
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  L'environnement virtuel n'existe pas. Création..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Environnement virtuel créé" -ForegroundColor Green
}

# Activer l'environnement virtuel
Write-Host "🔄 Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Mettre à jour pip
Write-Host "⬆️  Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Installer les dépendances
Write-Host "📥 Installation des dépendances depuis requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "✅ Installation terminée !" -ForegroundColor Green
Write-Host "💡 Vérifiez avec : pip list | Select-String ldap3" -ForegroundColor Cyan

