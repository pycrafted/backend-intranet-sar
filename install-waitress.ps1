# =============================================================================
# Script pour installer et vérifier Waitress (Windows)
# =============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Waitress (Windows)" -ForegroundColor Cyan
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

# Vérifier si Waitress est déjà installé
Write-Host "Vérification de Waitress..." -ForegroundColor Yellow
$waitressCheck = & python -c "import waitress; print(waitress.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Waitress est déjà installé (version: $waitressCheck)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour mettre à jour Waitress:" -ForegroundColor Cyan
    Write-Host "  pip install --upgrade waitress" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[INFO] Waitress n'est pas installé, installation en cours..." -ForegroundColor Yellow
    
    # Installer depuis requirements.txt
    if (Test-Path "requirements.txt") {
        Write-Host "Installation depuis requirements.txt..." -ForegroundColor Yellow
        & pip install -r requirements.txt
    } else {
        Write-Host "Installation directe de Waitress..." -ForegroundColor Yellow
        & pip install waitress
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Waitress installé avec succès" -ForegroundColor Green
        
        # Vérifier la version
        $version = & python -c "import waitress; print(waitress.__version__)" 2>&1
        Write-Host "Version installée: $version" -ForegroundColor Cyan
    } else {
        Write-Host "[ERREUR] Échec de l'installation de Waitress" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Vérification de la configuration..." -ForegroundColor Yellow

# Vérifier que le fichier de configuration existe
if (Test-Path "waitress_config.py") {
    Write-Host "[OK] Fichier de configuration trouvé: waitress_config.py" -ForegroundColor Green
} else {
    Write-Host "[ATTENTION] Fichier de configuration non trouvé: waitress_config.py" -ForegroundColor Yellow
    Write-Host "Créez-le avec les paramètres appropriés" -ForegroundColor Yellow
}

# Vérifier que wsgi.py existe
if (Test-Path "master\wsgi.py") {
    Write-Host "[OK] Fichier WSGI trouvé: master\wsgi.py" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Fichier WSGI non trouvé: master\wsgi.py" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "[OK] Installation terminée !" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour démarrer Waitress:" -ForegroundColor Cyan
Write-Host "  .\start-waitress.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Pour arrêter Waitress:" -ForegroundColor Cyan
Write-Host "  .\stop-waitress.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Documentation complète:" -ForegroundColor Cyan
Write-Host "  Voir README-WAITRESS.md" -ForegroundColor White
Write-Host ""
Write-Host "Note: Waitress est compatible Windows, contrairement à Gunicorn" -ForegroundColor Gray
Write-Host ""



