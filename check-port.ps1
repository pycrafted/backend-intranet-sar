# Script pour vérifier si un port est occupé
# Usage: .\check-port.ps1 [port]
# Exemple: .\check-port.ps1 8000

param(
    [int]$Port = 8000
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Vérification du port $Port" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Méthode 1: Utiliser netstat
Write-Host "Méthode 1: Utilisation de netstat" -ForegroundColor Yellow
Write-Host ""

$netstatResult = netstat -ano | Select-String ":$Port"

if ($netstatResult) {
    Write-Host "[OCCUPÉ] Le port $Port est utilisé par les processus suivants:" -ForegroundColor Red
    Write-Host ""
    
    foreach ($line in $netstatResult) {
        $lineStr = $line.ToString()
        Write-Host "  $lineStr" -ForegroundColor White
        
        # Extraire le PID (Process ID)
        if ($lineStr -match '\s+(\d+)\s*$') {
            $pid = $matches[1]
            
            # Obtenir les informations sur le processus
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "    └─> Processus: $($process.ProcessName) (PID: $pid)" -ForegroundColor Yellow
                    Write-Host "        Chemin: $($process.Path)" -ForegroundColor Gray
                }
            } catch {
                Write-Host "    └─> PID: $pid (processus peut ne plus exister)" -ForegroundColor Gray
            }
        }
    }
} else {
    Write-Host "[LIBRE] Le port $Port n'est pas utilisé" -ForegroundColor Green
}

Write-Host ""

# Méthode 2: Utiliser Get-NetTCPConnection (PowerShell moderne)
Write-Host "Méthode 2: Utilisation de Get-NetTCPConnection" -ForegroundColor Yellow
Write-Host ""

$connections = $null
try {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    
    if ($connections) {
        Write-Host "[OCCUPÉ] Le port $Port est utilisé:" -ForegroundColor Red
        Write-Host ""
        
        foreach ($conn in $connections) {
            Write-Host "  État: $($conn.State)" -ForegroundColor White
            Write-Host "  Adresse locale: $($conn.LocalAddress):$($conn.LocalPort)" -ForegroundColor White
            Write-Host "  Adresse distante: $($conn.RemoteAddress):$($conn.RemotePort)" -ForegroundColor White
            
            if ($conn.OwningProcess) {
                try {
                    $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Host "  Processus: $($process.ProcessName) (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
                        Write-Host "  Chemin: $($process.Path)" -ForegroundColor Gray
                    }
                } catch {
                    Write-Host "  PID: $($conn.OwningProcess)" -ForegroundColor Gray
                }
            }
            Write-Host ""
        }
    } else {
        Write-Host "[LIBRE] Le port $Port n'est pas utilisé" -ForegroundColor Green
    }
} catch {
    Write-Host "[INFO] Get-NetTCPConnection n'est pas disponible sur ce système" -ForegroundColor Yellow
}

Write-Host ""

# Méthode 3: Tester la connexion
Write-Host "Méthode 3: Test de connexion" -ForegroundColor Yellow
Write-Host ""

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $result = $tcpClient.BeginConnect("localhost", $Port, $null, $null)
    $wait = $result.AsyncWaitHandle.WaitOne(1000, $false)
    
    if ($wait) {
        try {
            $tcpClient.EndConnect($result)
            Write-Host "[OCCUPÉ] Le port $Port accepte les connexions" -ForegroundColor Red
        } catch {
            Write-Host "[LIBRE] Le port $Port n'accepte pas les connexions" -ForegroundColor Green
        }
    } else {
        Write-Host "[LIBRE] Le port $Port n'accepte pas les connexions (timeout)" -ForegroundColor Green
    }
    
    $tcpClient.Close()
} catch {
    Write-Host "[INFO] Test de connexion échoué: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Vérification terminée" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Résumé
Write-Host "Résumé:" -ForegroundColor Yellow
$isOccupied = $false
if ($netstatResult -or ($null -ne $connections -and $connections.Count -gt 0)) {
    $isOccupied = $true
    Write-Host "  Le port $Port est OCCUPÉ" -ForegroundColor Red
    Write-Host "  Vous devrez utiliser un autre port ou arrêter le processus qui l'utilise" -ForegroundColor Yellow
} else {
    Write-Host "  Le port $Port est LIBRE" -ForegroundColor Green
    Write-Host "  Vous pouvez l'utiliser pour votre serveur Django" -ForegroundColor Green
}

Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  # Voir tous les ports en écoute:" -ForegroundColor White
Write-Host "  netstat -ano | findstr LISTENING" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Vérifier un autre port:" -ForegroundColor White
Write-Host "  .\check-port.ps1 8001" -ForegroundColor Cyan
Write-Host ""

