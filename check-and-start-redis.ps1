# Script pour vérifier et démarrer Redis/Memurai

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Vérification et démarrage de Redis" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Chercher le service Memurai
$service = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if (-not $service) {
    # Chercher d'autres variantes
    $service = Get-Service -Name "Memurai*" -ErrorAction SilentlyContinue | Select-Object -First 1
}

if (-not $service) {
    Write-Host "[ERREUR] Service Memurai/Redis non trouvé!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Services Redis/Memurai disponibles:" -ForegroundColor Yellow
    Get-Service | Where-Object { $_.Name -like "*redis*" -or $_.Name -like "*memurai*" } | Format-Table Name, DisplayName, Status -AutoSize
    exit 1
}

Write-Host "Service trouvé: $($service.DisplayName) ($($service.Name))" -ForegroundColor Green
Write-Host "Statut actuel: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Running"){"Green"}else{"Yellow"})
Write-Host ""

# Si le service n'est pas en cours d'exécution, essayer de le démarrer
if ($service.Status -ne "Running") {
    Write-Host "Le service n'est pas en cours d'exécution. Tentative de démarrage..." -ForegroundColor Yellow
    
    if (-not $isAdmin) {
        Write-Host "[WARNING] Vous n'êtes pas administrateur. Le démarrage peut échouer." -ForegroundColor Yellow
        Write-Host "Pour démarrer le service, exécutez PowerShell en tant qu'administrateur." -ForegroundColor Yellow
        Write-Host ""
    }
    
    try {
        Start-Service -Name $service.Name -ErrorAction Stop
        Start-Sleep -Seconds 3
        
        $service = Get-Service -Name $service.Name
        if ($service.Status -eq "Running") {
            Write-Host "[OK] Service démarré avec succès!" -ForegroundColor Green
        } else {
            Write-Host "[ERREUR] Le service n'a pas démarré. Statut: $($service.Status)" -ForegroundColor Red
            if (-not $isAdmin) {
                Write-Host "[INFO] Essayez d'exécuter ce script en tant qu'administrateur." -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "[ERREUR] Impossible de démarrer le service: $_" -ForegroundColor Red
        if (-not $isAdmin) {
            Write-Host "[INFO] Exécutez PowerShell en tant qu'administrateur et réessayez." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[OK] Le service est déjà en cours d'exécution!" -ForegroundColor Green
}

# Vérifier que Redis écoute sur le port 6379
Write-Host ""
Write-Host "Vérification de l'écoute sur le port 6379..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
$listening = netstat -an | Select-String ":6379" | Select-String "LISTENING"

if ($listening) {
    Write-Host "[OK] Redis écoute sur le port 6379" -ForegroundColor Green
    foreach ($line in $listening) {
        Write-Host "  $line" -ForegroundColor White
    }
} else {
    Write-Host "[WARNING] Redis n'écoute pas encore sur le port 6379" -ForegroundColor Yellow
    Write-Host "  Attendez quelques secondes et réessayez." -ForegroundColor White
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Test de connexion..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Exécutez maintenant: python test_redis.py" -ForegroundColor Yellow
Write-Host ""










