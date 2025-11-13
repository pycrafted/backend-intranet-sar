# Script de diagnostic pour les ports 3000 et 8000
# Verifie l'etat des ports et identifie les processus qui les utilisent

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Diagnostic des ports 3000 et 8000" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function Get-PortInfo {
    param([int]$Port)
    
    Write-Host "Analyse du port $Port..." -ForegroundColor Yellow
    Write-Host ""
    
    # Verifier les connexions TCP
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    
    if ($connections) {
        Write-Host "   Connexions trouvees:" -ForegroundColor Cyan
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            $processName = if ($process) { $process.Name } else { "Inconnu" }
            $processPath = if ($process) { $process.Path } else { "N/A" }
            
            Write-Host "   - Etat: $($conn.State)" -ForegroundColor White
            Write-Host "     Processus: $processName (PID: $($conn.OwningProcess))" -ForegroundColor White
            Write-Host "     Chemin: $processPath" -ForegroundColor Gray
            $localAddr = "$($conn.LocalAddress):$($conn.LocalPort)"
            $remoteAddr = "$($conn.RemoteAddress):$($conn.RemotePort)"
            Write-Host "     Adresse locale: $localAddr" -ForegroundColor Gray
            Write-Host "     Adresse distante: $remoteAddr" -ForegroundColor Gray
            Write-Host ""
            
            # Si c'est le processus systeme (PID 4), c'est suspect
            if ($conn.OwningProcess -eq 4) {
                Write-Host "   ATTENTION: Le port est utilise par le processus systeme (PID 4)" -ForegroundColor Yellow
                Write-Host "      Cela peut indiquer un probleme de configuration reseau" -ForegroundColor Yellow
                Write-Host "      ou un service Windows qui ecoute sur ce port." -ForegroundColor Yellow
                Write-Host ""
            }
        }
    } else {
        Write-Host "   Port $Port : Aucune connexion active (port disponible)" -ForegroundColor Green
        Write-Host ""
    }
    
    # Verifier les regles de pare-feu
    Write-Host "   Regles de pare-feu pour le port $Port" -ForegroundColor Cyan
    $firewallRules = Get-NetFirewallRule | Where-Object {
        $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $_ -ErrorAction SilentlyContinue
        $portFilter -and $portFilter.LocalPort -eq $Port
    }
    
    if ($firewallRules) {
        foreach ($rule in $firewallRules) {
            $enabled = if ($rule.Enabled) { "Activee" } else { "Desactivee" }
            $action = if ($rule.Action -eq "Allow") { "Autoriser" } else { "Bloquer" }
            Write-Host "   - $($rule.DisplayName): $enabled, $action, $($rule.Direction)" -ForegroundColor White
        }
    } else {
        Write-Host "   Aucune regle de pare-feu trouvee pour ce port" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Analyser les deux ports
Get-PortInfo -Port 3000
Get-PortInfo -Port 8000

# Verifier l'etat du pare-feu Windows
Write-Host "Etat du pare-feu Windows:" -ForegroundColor Cyan
$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    $status = if ($profile.Enabled) { "Active" } else { "Desactive" }
    Write-Host "   - $($profile.Name): $status" -ForegroundColor White
}
Write-Host ""

# Verifier les services qui pourraient utiliser ces ports
Write-Host "Services Windows susceptibles d'utiliser ces ports:" -ForegroundColor Cyan
$suspiciousServices = @("HTTP", "W3SVC", "World Wide Web Publishing Service", "IIS Admin Service")
foreach ($serviceName in $suspiciousServices) {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        $status = $service.Status
        Write-Host "   - $serviceName : $status" -ForegroundColor White
    }
}
Write-Host ""

# Recommandations
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Recommandations:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Si les ports sont utilises par le processus systeme (PID 4):" -ForegroundColor Yellow
Write-Host "   - Verifiez si IIS ou un autre service web est actif" -ForegroundColor White
Write-Host "   - Arretez les services inutiles: Stop-Service W3SVC" -ForegroundColor White
Write-Host "   - Ou utilisez des ports differents (ex: 3001, 8001)" -ForegroundColor White
Write-Host ""
Write-Host "2. Si les ports sont bloques par le pare-feu:" -ForegroundColor Yellow
Write-Host "   - Executez le script debloquer-ports.ps1 en tant qu'administrateur" -ForegroundColor White
Write-Host ""
Write-Host "3. Pour liberer un port utilise:" -ForegroundColor Yellow
Write-Host "   - Identifiez le PID du processus" -ForegroundColor White
Write-Host "   - Arretez le processus: Stop-Process -Id [PID] -Force" -ForegroundColor White
Write-Host "   - OU arretez le service correspondant" -ForegroundColor White
Write-Host ""
