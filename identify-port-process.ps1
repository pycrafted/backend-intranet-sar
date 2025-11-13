# Script pour identifier le processus/service qui utilise un port
# Usage: .\identify-port-process.ps1 [port]
# Exemple: .\identify-port-process.ps1 8000

param(
    [int]$Port = 8000
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Identification du processus sur le port $Port" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Obtenir les connexions sur le port
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "[INFO] Aucune connexion trouvée sur le port $Port" -ForegroundColor Yellow
    exit 0
}

Write-Host "Connexions trouvees sur le port ${Port}:" -ForegroundColor Yellow
Write-Host ""

foreach ($conn in $connections) {
    $processId = $conn.OwningProcess
    
    Write-Host "PID: $processId" -ForegroundColor Cyan
    Write-Host "  État: $($conn.State)" -ForegroundColor White
    Write-Host "  Adresse locale: $($conn.LocalAddress):$($conn.LocalPort)" -ForegroundColor White
    
    # Obtenir les informations du processus
    try {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  Nom du processus: $($process.ProcessName)" -ForegroundColor Green
            Write-Host "  Chemin: $($process.Path)" -ForegroundColor Gray
            
            # Pour le PID 4 (System), chercher les services qui pourraient utiliser le port
            if ($processId -eq 4) {
                Write-Host ""
                Write-Host "  [INFO] PID 4 = Processus System (processus système Windows)" -ForegroundColor Yellow
                Write-Host "  Recherche des services qui pourraient utiliser ce port..." -ForegroundColor Yellow
                Write-Host ""
                
                # Vérifier si IIS est installé et actif
                $iisService = Get-Service -Name "W3SVC" -ErrorAction SilentlyContinue
                if ($iisService) {
                    Write-Host "  ✓ IIS (World Wide Web Publishing Service) est installé" -ForegroundColor Green
                    Write-Host "    État: $($iisService.Status)" -ForegroundColor White
                    if ($iisService.Status -eq 'Running') {
                        Write-Host "    → IIS est probablement le service qui utilise le port $Port" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "  ✗ IIS n'est pas installé" -ForegroundColor Gray
                }
                
                # Vérifier d'autres services web courants
                $httpService = Get-Service -Name "HTTP" -ErrorAction SilentlyContinue
                if ($httpService) {
                    Write-Host "  ✓ Service HTTP (http.sys) est actif" -ForegroundColor Green
                    Write-Host "    État: $($httpService.Status)" -ForegroundColor White
                }
                
                # Lister les sites IIS s'ils existent
                try {
                    Import-Module WebAdministration -ErrorAction SilentlyContinue
                    $sites = Get-Website -ErrorAction SilentlyContinue
                    if ($sites) {
                        Write-Host ""
                        Write-Host "  Sites IIS configurés:" -ForegroundColor Cyan
                        foreach ($site in $sites) {
                            $bindings = Get-WebBinding -Name $site.Name
                            foreach ($binding in $bindings) {
                                $bindingInfo = $binding.bindingInformation
                                if ($bindingInfo -match ":${Port}") {
                                    Write-Host "    → Site: $($site.Name) utilise le port $Port" -ForegroundColor Yellow
                                    Write-Host "      Binding: $bindingInfo" -ForegroundColor Gray
                                }
                            }
                        }
                    }
                } catch {
                    # Module WebAdministration non disponible
                }
                
                # Vérifier avec netstat pour plus de détails
                Write-Host ""
                Write-Host "  Détails supplémentaires (netstat):" -ForegroundColor Cyan
                $netstatInfo = netstat -ano | Select-String ":${Port}" | Select-String "LISTENING"
                foreach ($line in $netstatInfo) {
                    Write-Host "    $line" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  [ERREUR] Impossible d'obtenir les informations du processus PID $processId" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERREUR] $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Résumé" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si c'est probablement IIS
$iisService = Get-Service -Name "W3SVC" -ErrorAction SilentlyContinue
if ($iisService -and $iisService.Status -eq 'Running') {
    Write-Host "Le port $Port est probablement utilisé par IIS (Internet Information Services)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour arrêter IIS (si nécessaire):" -ForegroundColor Cyan
    Write-Host "  Stop-Service -Name W3SVC" -ForegroundColor White
    Write-Host ""
    Write-Host "Pour désactiver IIS au démarrage:" -ForegroundColor Cyan
    Write-Host "  Set-Service -Name W3SVC -StartupType Disabled" -ForegroundColor White
} else {
    Write-Host "Le port $Port est utilisé par le processus System (PID 4)" -ForegroundColor Yellow
    Write-Host "Cela peut être un service système Windows ou un autre service" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Recommandation: Utilisez un autre port pour Django (ex: 8001)" -ForegroundColor Green
Write-Host ""

