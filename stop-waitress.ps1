# =============================================================================
# Script PowerShell pour arrêter Waitress
# =============================================================================

Write-Host "Arrêt de Waitress..." -ForegroundColor Yellow

# Port à utiliser
$port = $env:WAITRESS_PORT
if (-not $port) {
    $port = "8001"
}

Write-Host "Recherche des processus Waitress sur le port $port..." -ForegroundColor Yellow

# Trouver le processus qui écoute sur le port
$netstat = netstat -ano | Select-String ":$port.*LISTENING"
$pidsToStop = @()

if ($netstat) {
    foreach ($line in $netstat) {
        $parts = $line -split '\s+'
        $pid = $parts[-1]
        if ($pid -and $pid -match '^\d+$') {
            $pidsToStop += [int]$pid
        }
    }
}

# Chercher aussi les processus Python qui pourraient être Waitress
if ($pidsToStop.Count -eq 0) {
    Write-Host "Recherche alternative des processus Python..." -ForegroundColor Yellow
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    foreach ($proc in $pythonProcesses) {
        # Vérifier si le processus écoute sur le port
        $procNetstat = netstat -ano | Select-String ":$port.*LISTENING.*$($proc.Id)"
        if ($procNetstat) {
            $pidsToStop += $proc.Id
        }
    }
}

if ($pidsToStop.Count -gt 0) {
    foreach ($pid in $pidsToStop) {
        Write-Host "Arrêt du processus Waitress (PID: $pid)..." -ForegroundColor Yellow
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $pid -Force
                Write-Host "[OK] Processus $pid arrêté" -ForegroundColor Green
            }
        } catch {
            Write-Host "[ERREUR] Impossible d'arrêter le processus $pid : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[INFO] Aucun processus Waitress trouvé sur le port $port" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Vérification..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
$remaining = netstat -ano | Select-String ":$port.*LISTENING"
if ($remaining) {
    Write-Host "[ATTENTION] Le port $port est toujours utilisé" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Waitress arrêté" -ForegroundColor Green
}



