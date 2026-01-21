# =============================================================================
# Script pour installer et vérifier Gunicorn
# =============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Gunicorn" -ForegroundColor Cyan
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

# Vérifier si Gunicorn est déjà installé
Write-Host "Vérification de Gunicorn..." -ForegroundColor Yellow
$gunicornCheck = & python -c "import gunicorn; print(gunicorn.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Gunicorn est déjà installé (version: $gunicornCheck)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour mettre à jour Gunicorn:" -ForegroundColor Cyan
    Write-Host "  pip install --upgrade gunicorn" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[INFO] Gunicorn n'est pas installé, installation en cours..." -ForegroundColor Yellow
    
    # Installer depuis requirements.txt
    if (Test-Path "requirements.txt") {
        Write-Host "Installation depuis requirements.txt..." -ForegroundColor Yellow
        & pip install -r requirements.txt
    } else {
        Write-Host "Installation directe de Gunicorn..." -ForegroundColor Yellow
        & pip install gunicorn
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Gunicorn installé avec succès" -ForegroundColor Green
        
        # Vérifier la version
        $version = & python -c "import gunicorn; print(gunicorn.__version__)" 2>&1
        Write-Host "Version installée: $version" -ForegroundColor Cyan
    } else {
        Write-Host "[ERREUR] Échec de l'installation de Gunicorn" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Vérification de la configuration..." -ForegroundColor Yellow

# Vérifier que le fichier de configuration existe
if (Test-Path "gunicorn_config.py") {
    Write-Host "[OK] Fichier de configuration trouvé: gunicorn_config.py" -ForegroundColor Green
} else {
    Write-Host "[ATTENTION] Fichier de configuration non trouvé: gunicorn_config.py" -ForegroundColor Yellow
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
Write-Host "Pour démarrer Gunicorn:" -ForegroundColor Cyan
Write-Host "  .\start-gunicorn.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Pour arrêter Gunicorn:" -ForegroundColor Cyan
Write-Host "  .\stop-gunicorn.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Documentation complète:" -ForegroundColor Cyan
Write-Host "  Voir README-GUNICORN.md" -ForegroundColor White
Write-Host ""



