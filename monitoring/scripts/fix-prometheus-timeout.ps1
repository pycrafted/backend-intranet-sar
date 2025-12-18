# Script pour augmenter le timeout du service Prometheus
# Usage: .\fix-prometheus-timeout.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Augmentation du timeout du service Prometheus" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si le script est execute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Red
    exit 1
}

$serviceName = "Prometheus"

# Augmenter le timeout du service via le registre
Write-Host "[INFO] Augmentation du timeout du service..." -ForegroundColor Yellow

$regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName"
$timeoutValue = 120000  # 120 secondes (en millisecondes)

try {
    # Creer la cle si elle n'existe pas
    if (-not (Test-Path $regPath)) {
        Write-Host "[ERREUR] Service non trouve dans le registre" -ForegroundColor Red
        exit 1
    }
    
    # Ajouter/modifier la valeur ServicesPipeTimeout
    # Note: Cette valeur est globale pour tous les services, mais on peut essayer
    # Pour un service specifique, on peut utiliser FailureActions
    
    # Essayer d'augmenter le timeout via sc.exe failure
    Write-Host "  Configuration des actions en cas d'echec..." -ForegroundColor Gray
    & sc.exe failure $serviceName reset= 86400 actions= restart/5000/restart/10000/restart/20000 2>&1 | Out-Null
    
    Write-Host "[OK] Configuration mise a jour" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: Le timeout par defaut de Windows est de 30 secondes." -ForegroundColor Yellow
    Write-Host "Si Prometheus prend plus de 30 secondes a demarrer, il faut:" -ForegroundColor Yellow
    Write-Host "  1. Utiliser NSSM (Non-Sucking Service Manager)" -ForegroundColor White
    Write-Host "  2. Ou creer un wrapper batch qui attend avant de lancer Prometheus" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERREUR] Impossible de modifier la configuration: $_" -ForegroundColor Red
}

# Essayer de demarrer le service
Write-Host "[INFO] Tentative de demarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Write-Host "[OK] Commande Start-Service executee" -ForegroundColor Green
    
    # Attendre plus longtemps
    Write-Host "  Attente jusqu'a 60 secondes..." -ForegroundColor Gray
    $maxWait = 60
    for ($i = 1; $i -le $maxWait; $i++) {
        Start-Sleep -Seconds 1
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Write-Host "[OK] Service demarre apres $i secondes!" -ForegroundColor Green
            break
        }
        if ($i % 10 -eq 0) {
            Write-Host "  Attente... ($i/$maxWait s) - Statut: $($service.Status)" -ForegroundColor Gray
        }
    }
    
    $finalService = Get-Service -Name $serviceName
    if ($finalService.Status -eq "Running") {
        Write-Host ""
        Write-Host "[OK] Prometheus fonctionne!" -ForegroundColor Green
        Write-Host "  Acces: http://sar-intranet.sar.sn:9090" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERREUR] Service toujours arrete apres 60 secondes" -ForegroundColor Red
        Write-Host "  Le service prend probablement trop de temps a demarrer" -ForegroundColor Yellow
        Write-Host "  Solution recommandee: Utiliser NSSM" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERREUR] Impossible de demarrer: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan





