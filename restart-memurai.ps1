# Script pour redémarrer le service Memurai et vérifier les erreurs

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Redémarrage du service Memurai" -ForegroundColor Cyan
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
    exit 1
}

Write-Host "Statut actuel: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Vérifier les logs d'erreur récents
Write-Host "Vérification des logs d'erreur..." -ForegroundColor Yellow
$errors = Get-EventLog -LogName Application -Source "Memurai" -Newest 5 -ErrorAction SilentlyContinue

if ($errors) {
    Write-Host "[WARNING] Erreurs récentes trouvées:" -ForegroundColor Yellow
    foreach ($error in $errors) {
        Write-Host "  [$($error.TimeGenerated)] $($error.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# Vérifier le fichier de configuration
$configFile = "C:\Program Files\Memurai\memurai.conf"
if (Test-Path $configFile) {
    Write-Host "Vérification de la syntaxe du fichier de configuration..." -ForegroundColor Yellow
    
    # Vérifier que requirepass a une valeur
    $configContent = Get-Content $configFile -Raw
    if ($configContent -match '(?m)^\s*requirepass\s*$') {
        Write-Host "[ERREUR] La directive requirepass n'a pas de valeur!" -ForegroundColor Red
        Write-Host "  Corrigez le fichier: $configFile" -ForegroundColor Yellow
    } elseif ($configContent -match '(?m)^\s*requirepass\s+(.+)$') {
        $password = $matches[1].Trim()
        Write-Host "[OK] Mot de passe configuré dans memurai.conf" -ForegroundColor Green
    }
}

# Essayer de démarrer le service
Write-Host ""
Write-Host "Démarrage du service Memurai..." -ForegroundColor Yellow

try {
    Start-Service -Name "Memurai" -ErrorAction Stop
    Start-Sleep -Seconds 3
    
    $service = Get-Service -Name "Memurai"
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service Memurai démarré avec succès!" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Le service n'a pas démarré. Statut: $($service.Status)" -ForegroundColor Red
        
        # Vérifier les logs d'erreur immédiatement après
        Start-Sleep -Seconds 1
        $recentErrors = Get-EventLog -LogName Application -Source "Memurai" -Newest 1 -ErrorAction SilentlyContinue
        if ($recentErrors) {
            Write-Host ""
            Write-Host "Dernière erreur:" -ForegroundColor Red
            Write-Host "  $($recentErrors[0].Message)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "[ERREUR] Impossible de démarrer le service: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Vérifiez:" -ForegroundColor Yellow
    Write-Host "  1. Le fichier de configuration memurai.conf est valide" -ForegroundColor White
    Write-Host "  2. Aucun autre processus n'utilise le port 6379" -ForegroundColor White
    Write-Host "  3. Les permissions sur le dossier Memurai sont correctes" -ForegroundColor White
    Write-Host ""
    Write-Host "Pour voir les logs détaillés:" -ForegroundColor Yellow
    Write-Host "  Get-EventLog -LogName Application -Source 'Memurai' -Newest 10" -ForegroundColor White
}

# Vérifier que Redis écoute
Write-Host ""
Write-Host "Vérification de l'écoute Redis..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
$listening = netstat -an | Select-String ":6379" | Select-String "LISTENING"

if ($listening) {
    Write-Host "[OK] Redis écoute sur le port 6379" -ForegroundColor Green
    foreach ($line in $listening) {
        Write-Host "  $line" -ForegroundColor White
    }
} else {
    Write-Host "[WARNING] Redis n'écoute pas sur le port 6379" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan

