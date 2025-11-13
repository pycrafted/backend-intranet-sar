# Script d'installation de Redis (Memurai) pour Windows Server 2022
# Ce script installe Memurai, une version native de Redis pour Windows

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Redis (Memurai) pour Windows" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Option 1: Installation via Chocolatey (recommandé si Chocolatey est installé)
Write-Host "Méthode 1: Installation via Chocolatey" -ForegroundColor Yellow
Write-Host ""

# Vérifier si Chocolatey est installé
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
if ($chocoInstalled) {
    Write-Host "[OK] Chocolatey est installé" -ForegroundColor Green
    Write-Host "Installation de Memurai via Chocolatey..." -ForegroundColor Yellow
    
    try {
        choco install memurai-developer -y
        Write-Host "[OK] Memurai installé avec succès via Chocolatey!" -ForegroundColor Green
        $installed = $true
    } catch {
        Write-Host "[ERREUR] Échec de l'installation via Chocolatey: $_" -ForegroundColor Red
        $installed = $false
    }
} else {
    Write-Host "[INFO] Chocolatey n'est pas installé" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Voulez-vous installer Chocolatey? (O/N)" -ForegroundColor Cyan
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        Write-Host "Installation de Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-Host "[OK] Chocolatey installé avec succès!" -ForegroundColor Green
            choco install memurai-developer -y
            $installed = $true
        } else {
            Write-Host "[ERREUR] Échec de l'installation de Chocolatey" -ForegroundColor Red
            $installed = $false
        }
    } else {
        $installed = $false
    }
}

# Option 2: Installation manuelle si Chocolatey a échoué
if (-not $installed) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Méthode 2: Installation manuelle" -ForegroundColor Yellow
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Instructions pour l'installation manuelle:" -ForegroundColor Yellow
    Write-Host "1. Téléchargez Memurai depuis: https://www.memurai.com/get-memurai" -ForegroundColor White
    Write-Host "2. Exécutez l'installateur téléchargé" -ForegroundColor White
    Write-Host "3. Suivez les instructions d'installation" -ForegroundColor White
    Write-Host "4. Le service Memurai démarrera automatiquement" -ForegroundColor White
    Write-Host ""
    Write-Host "OU" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Alternative: Utiliser Redis pour Windows (version non officielle)" -ForegroundColor Yellow
    Write-Host "Téléchargez depuis: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
    Write-Host ""
    
    $manual = Read-Host "Avez-vous installé Memurai manuellement? (O/N)"
    if ($manual -eq "O" -or $manual -eq "o") {
        $installed = $true
    }
}

# Vérifier si Redis/Memurai est installé et fonctionne
if ($installed) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Vérification de l'installation" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Vérifier le service Memurai
    $memuraiService = Get-Service -Name "Memurai*" -ErrorAction SilentlyContinue
    if ($memuraiService) {
        Write-Host "[OK] Service Memurai trouvé: $($memuraiService.Name)" -ForegroundColor Green
        
        if ($memuraiService.Status -eq "Running") {
            Write-Host "[OK] Service Memurai est en cours d'exécution" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Démarrage du service Memurai..." -ForegroundColor Yellow
            Start-Service -Name $memuraiService.Name
            Start-Sleep -Seconds 2
            if ((Get-Service -Name $memuraiService.Name).Status -eq "Running") {
                Write-Host "[OK] Service Memurai démarré avec succès" -ForegroundColor Green
            } else {
                Write-Host "[ERREUR] Impossible de démarrer le service Memurai" -ForegroundColor Red
            }
        }
    } else {
        # Vérifier Redis (version alternative)
        $redisService = Get-Service -Name "Redis*" -ErrorAction SilentlyContinue
        if ($redisService) {
            Write-Host "[OK] Service Redis trouvé: $($redisService.Name)" -ForegroundColor Green
            if ($redisService.Status -ne "Running") {
                Start-Service -Name $redisService.Name
            }
        } else {
            Write-Host "[WARNING] Aucun service Redis/Memurai trouvé" -ForegroundColor Yellow
            Write-Host "Le service peut avoir un nom différent. Vérifiez manuellement." -ForegroundColor Yellow
        }
    }
    
    # Test de connexion Redis
    Write-Host ""
    Write-Host "Test de connexion Redis..." -ForegroundColor Yellow
    
    # Vérifier si redis-cli est disponible
    $redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
    if ($redisCli) {
        try {
            $pingResult = redis-cli ping
            if ($pingResult -eq "PONG") {
                Write-Host "[OK] Connexion Redis réussie!" -ForegroundColor Green
            } else {
                Write-Host "[WARNING] Redis répond mais avec un résultat inattendu: $pingResult" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERREUR] Impossible de se connecter à Redis: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[INFO] redis-cli n'est pas dans le PATH" -ForegroundColor Yellow
        Write-Host "Vous pouvez tester la connexion depuis Python avec le script test_redis.py" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Paramètres Redis par défaut:" -ForegroundColor Yellow
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 6379" -ForegroundColor White
Write-Host "  Database: 0" -ForegroundColor White
Write-Host "  Password: (aucun par défaut)" -ForegroundColor White
Write-Host ""
Write-Host "N'oubliez pas de configurer ces paramètres dans votre fichier .env!" -ForegroundColor Yellow
Write-Host ""

