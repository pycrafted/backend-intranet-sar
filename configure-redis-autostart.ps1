# Script pour configurer Memurai (Redis) pour démarrer automatiquement au démarrage de Windows
# Ce script vérifie et configure le service pour qu'il démarre automatiquement

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration du démarrage automatique Redis" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

$service = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "[ERREUR] Service Memurai non trouvé!" -ForegroundColor Red
    Write-Host "Redis n'est peut-être pas installé correctement." -ForegroundColor Yellow
    exit 1
}

Write-Host "Service trouvé: $($service.DisplayName)" -ForegroundColor Green
Write-Host "Statut actuel: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Vérifier le type de démarrage actuel
$serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$($service.Name)'"
$startType = $serviceWmi.StartMode

Write-Host "Type de démarrage actuel: $startType" -ForegroundColor Yellow
Write-Host ""

# Types de démarrage possibles:
# - Automatic : Démarre automatiquement au démarrage de Windows
# - Manual : Doit être démarré manuellement
# - Disabled : Désactivé, ne peut pas être démarré

if ($startType -eq "Automatic") {
    Write-Host "[OK] Redis est déjà configuré pour démarrer automatiquement!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Après un redémarrage du serveur Windows:" -ForegroundColor Yellow
    Write-Host "  ✓ Redis démarrera automatiquement" -ForegroundColor Green
    Write-Host "  ✓ Aucune action manuelle nécessaire" -ForegroundColor Green
} else {
    Write-Host "[INFO] Configuration du démarrage automatique..." -ForegroundColor Yellow
    
    try {
        # Configurer le service pour démarrer automatiquement
        Set-Service -Name $service.Name -StartupType Automatic -ErrorAction Stop
        Write-Host "[OK] Redis configuré pour démarrer automatiquement!" -ForegroundColor Green
        
        # Si le service n'est pas en cours d'exécution, le démarrer
        if ($service.Status -ne "Running") {
            Write-Host ""
            Write-Host "Démarrage du service..." -ForegroundColor Yellow
            Start-Service -Name $service.Name -ErrorAction Stop
            Start-Sleep -Seconds 2
            
            $service = Get-Service -Name $service.Name
            if ($service.Status -eq "Running") {
                Write-Host "[OK] Service démarré avec succès" -ForegroundColor Green
            }
        }
        
        Write-Host ""
        Write-Host "Configuration terminée!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Après un redémarrage du serveur Windows:" -ForegroundColor Yellow
        Write-Host "  ✓ Redis démarrera automatiquement" -ForegroundColor Green
        Write-Host "  ✓ Aucune action manuelle nécessaire" -ForegroundColor Green
        
    } catch {
        Write-Host "[ERREUR] Impossible de configurer le démarrage automatique: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Vous pouvez le faire manuellement avec:" -ForegroundColor Yellow
        Write-Host "  Set-Service -Name 'Memurai' -StartupType Automatic" -ForegroundColor White
        exit 1
    }
}

# Vérification finale
Write-Host ""
Write-Host "Vérification finale..." -ForegroundColor Yellow
$serviceWmi = Get-WmiObject -Class Win32_Service -Filter "Name='$($service.Name)'"
$finalStartType = $serviceWmi.StartMode
$finalStatus = (Get-Service -Name $service.Name).Status

Write-Host "  Type de démarrage: $finalStartType" -ForegroundColor $(if($finalStartType -eq "Automatic"){"Green"}else{"Yellow"})
Write-Host "  Statut actuel: $finalStatus" -ForegroundColor $(if($finalStatus -eq "Running"){"Green"}else{"Yellow"})

# Test de connexion Redis
Write-Host ""
Write-Host "Test de connexion Redis..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
$listening = netstat -an | Select-String ":6379" | Select-String "LISTENING"

if ($listening) {
    Write-Host "[OK] Redis écoute sur le port 6379" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Redis n'écoute pas encore sur le port 6379" -ForegroundColor Yellow
    Write-Host "  Attendez quelques secondes et vérifiez avec: netstat -an | findstr :6379" -ForegroundColor White
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Résumé:" -ForegroundColor Yellow
Write-Host "  ✓ Redis démarrera automatiquement après un redémarrage Windows" -ForegroundColor Green
Write-Host "  ✓ Aucune intervention manuelle nécessaire" -ForegroundColor Green
Write-Host ""
Write-Host "Pour vérifier le type de démarrage à tout moment:" -ForegroundColor Yellow
Write-Host "  Get-Service -Name 'Memurai' | Select-Object Name, Status, StartType" -ForegroundColor White
Write-Host ""

