# Script pour debloquer les ports 3000 et 8000 dans le pare-feu Windows
# A executer en tant qu'administrateur

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deblocage des ports 3000 et 8000" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si le script est execute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ATTENTION: Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Yellow
    Write-Host "   Veuillez relancer PowerShell en tant qu'administrateur et reexecuter ce script." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Clic droit sur PowerShell > Executer en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

# Fonction pour creer ou mettre a jour une regle de pare-feu
function Set-FirewallRule {
    param(
        [string]$RuleName,
        [int]$Port,
        [string]$Direction = "Inbound"
    )
    
    Write-Host "Configuration du port $Port ($RuleName)..." -ForegroundColor Yellow
    
    # Verifier si la regle existe deja
    $existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Write-Host "   Regle existante trouvee, mise a jour..." -ForegroundColor Gray
        # Supprimer l'ancienne regle
        Remove-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    }
    
    # Creer la nouvelle regle
    try {
        New-NetFirewallRule `
            -DisplayName $RuleName `
            -Name $RuleName `
            -Direction $Direction `
            -Protocol TCP `
            -LocalPort $Port `
            -Action Allow `
            -Enabled True `
            -Profile Any `
            -ErrorAction Stop
        
        Write-Host "   Regle creee/activee avec succes pour le port $Port" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "   Erreur lors de la creation de la regle: $_" -ForegroundColor Red
        return $false
    }
}

# Fonction pour verifier l'etat d'un port
function Test-Port {
    param([int]$Port)
    
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "   Port $Port : Utilise par le processus $($process.Name) (PID: $($listener.OwningProcess))" -ForegroundColor Cyan
    } else {
        Write-Host "   Port $Port : Disponible" -ForegroundColor Green
    }
}

Write-Host "Etat actuel des ports:" -ForegroundColor Cyan
Test-Port -Port 3000
Test-Port -Port 8000
Write-Host ""

# Creer les regles de pare-feu pour les ports entrants
Write-Host "Configuration des regles de pare-feu..." -ForegroundColor Cyan
Write-Host ""

$success1 = Set-FirewallRule -RuleName "Intranet-Port-3000-Inbound" -Port 3000 -Direction "Inbound"
$success2 = Set-FirewallRule -RuleName "Intranet-Port-8000-Inbound" -Port 8000 -Direction "Inbound"

# Creer aussi les regles pour les ports sortants (au cas ou)
$success3 = Set-FirewallRule -RuleName "Intranet-Port-3000-Outbound" -Port 3000 -Direction "Outbound"
$success4 = Set-FirewallRule -RuleName "Intranet-Port-8000-Outbound" -Port 8000 -Direction "Outbound"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
if ($success1 -and $success2 -and $success3 -and $success4) {
    Write-Host "Toutes les regles ont ete configurees avec succes!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Regles creees:" -ForegroundColor Cyan
    Write-Host "   - Intranet-Port-3000-Inbound (TCP 3000)" -ForegroundColor White
    Write-Host "   - Intranet-Port-8000-Inbound (TCP 8000)" -ForegroundColor White
    Write-Host "   - Intranet-Port-3000-Outbound (TCP 3000)" -ForegroundColor White
    Write-Host "   - Intranet-Port-8000-Outbound (TCP 8000)" -ForegroundColor White
} else {
    Write-Host "Certaines regles n'ont pas pu etre creees" -ForegroundColor Yellow
    Write-Host "   Verifiez les messages d'erreur ci-dessus" -ForegroundColor Yellow
}
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Afficher les regles creees
Write-Host "Verification des regles creees:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "Intranet-Port-*" | Format-Table DisplayName, Enabled, Direction, Action -AutoSize

Write-Host ""
Write-Host "Conseil: Si les ports sont toujours bloques, verifiez:" -ForegroundColor Yellow
Write-Host "   1. Que le service Windows Firewall est actif" -ForegroundColor White
Write-Host "   2. Qu'aucun autre pare-feu (antivirus, etc.) ne bloque ces ports" -ForegroundColor White
Write-Host "   3. Que vous avez les permissions necessaires sur le serveur" -ForegroundColor White
Write-Host ""


