# Script pour changer le port d'IIS
# Usage: .\change-iis-port.ps1 [nouveau_port] [site_name]
# Exemple: .\change-iis-port.ps1 8080 "Default Web Site"

param(
    [int]$NewPort = 8080,
    [string]$SiteName = "Default Web Site"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Changement du port IIS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si IIS est installé
$iisService = Get-Service -Name "W3SVC" -ErrorAction SilentlyContinue
if (-not $iisService) {
    Write-Host "[ERREUR] IIS n'est pas installe sur ce serveur" -ForegroundColor Red
    Write-Host "Installez IIS d'abord avec:" -ForegroundColor Yellow
    Write-Host "  Install-WindowsFeature -Name Web-Server" -ForegroundColor White
    exit 1
}

Write-Host "[OK] IIS est installe" -ForegroundColor Green
Write-Host ""

# Importer le module WebAdministration
try {
    Import-Module WebAdministration -ErrorAction Stop
    Write-Host "[OK] Module WebAdministration charge" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Impossible de charger le module WebAdministration" -ForegroundColor Red
    Write-Host "Installez-le avec:" -ForegroundColor Yellow
    Write-Host "  Install-WindowsFeature -Name IIS-ManagementConsole" -ForegroundColor White
    exit 1
}

Write-Host ""

# Lister les sites existants
Write-Host "Sites IIS existants:" -ForegroundColor Yellow
$sites = Get-Website
foreach ($site in $sites) {
    Write-Host "  - $($site.Name) (Port: $($site.bindings.Collection.bindingInformation))" -ForegroundColor White
}

Write-Host ""

# Vérifier si le site existe
$site = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
if (-not $site) {
    Write-Host "[ERREUR] Le site '$SiteName' n'existe pas" -ForegroundColor Red
    Write-Host ""
    Write-Host "Sites disponibles:" -ForegroundColor Yellow
    foreach ($s in $sites) {
        Write-Host "  - $($s.Name)" -ForegroundColor White
    }
    exit 1
}

Write-Host "[OK] Site trouve: $SiteName" -ForegroundColor Green
Write-Host ""

# Obtenir les bindings actuels
$bindings = Get-WebBinding -Name $SiteName
Write-Host "Bindings actuels:" -ForegroundColor Yellow
foreach ($binding in $bindings) {
    Write-Host "  - $($binding.bindingInformation)" -ForegroundColor White
}

Write-Host ""

# Demander confirmation
Write-Host "Voulez-vous changer le port du site '$SiteName' vers $NewPort ?" -ForegroundColor Yellow
$confirmation = Read-Host "Tapez 'O' pour confirmer"

if ($confirmation -ne 'O' -and $confirmation -ne 'o') {
    Write-Host "Operation annulee" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Changer le port pour chaque binding HTTP
$changed = $false
foreach ($binding in $bindings) {
    if ($binding.protocol -eq 'http') {
        $bindingInfo = $binding.bindingInformation
        $parts = $bindingInfo -split ':'
        
        if ($parts.Length -ge 3) {
            $oldPort = $parts[1]
            $hostHeader = $parts[2]
            
            Write-Host "Changement du port de $oldPort vers $NewPort..." -ForegroundColor Yellow
            
            # Supprimer l'ancien binding
            Remove-WebBinding -Name $SiteName -Protocol http -BindingInformation $bindingInfo
            
            # Créer le nouveau binding
            $newBindingInfo = "*:${NewPort}:$hostHeader"
            New-WebBinding -Name $SiteName -Protocol http -BindingInformation $newBindingInfo
            
            Write-Host "[OK] Port change de $oldPort vers $NewPort" -ForegroundColor Green
            $changed = $true
        } else {
            # Format simple : *:8000:
            Write-Host "Changement du port vers $NewPort..." -ForegroundColor Yellow
            
            Remove-WebBinding -Name $SiteName -Protocol http -BindingInformation $bindingInfo
            
            $newBindingInfo = "*:${NewPort}:"
            New-WebBinding -Name $SiteName -Protocol http -BindingInformation $newBindingInfo
            
            Write-Host "[OK] Port change vers $NewPort" -ForegroundColor Green
            $changed = $true
        }
    }
}

if (-not $changed) {
    Write-Host "[INFO] Aucun binding HTTP trouve. Creation d'un nouveau binding sur le port $NewPort..." -ForegroundColor Yellow
    New-WebBinding -Name $SiteName -Protocol http -BindingInformation "*:${NewPort}:"
    Write-Host "[OK] Nouveau binding cree sur le port $NewPort" -ForegroundColor Green
}

Write-Host ""

# Afficher les nouveaux bindings
Write-Host "Nouveaux bindings:" -ForegroundColor Yellow
$newBindings = Get-WebBinding -Name $SiteName
foreach ($binding in $newBindings) {
    Write-Host "  - $($binding.bindingInformation)" -ForegroundColor White
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Port IIS change avec succes!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Le site '$SiteName' utilise maintenant le port $NewPort" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Assurez-vous que le port $NewPort est ouvert dans le pare-feu Windows!" -ForegroundColor Yellow
Write-Host "  New-NetFirewallRule -DisplayName 'IIS Port $NewPort' -Direction Inbound -LocalPort $NewPort -Protocol TCP -Action Allow" -ForegroundColor White
Write-Host ""

