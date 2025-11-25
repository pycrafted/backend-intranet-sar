# Test de demarrage manuel de Prometheus avec les memes arguments que le service
# Usage: .\test-prometheus-manual.ps1

$prometheusExe = "C:\Prometheus\prometheus.exe"
$configPath = "C:\Prometheus\prometheus.yml"
$dataDir = "C:\Prometheus\data"
$port = 9090
$retentionDays = 30

Write-Host "Test de demarrage manuel de Prometheus..." -ForegroundColor Yellow
Write-Host ""

$arguments = @(
    "--config.file=$configPath",
    "--storage.tsdb.path=$dataDir",
    "--storage.tsdb.retention.time=${retentionDays}d",
    "--web.listen-address=0.0.0.0:$port"
)

Write-Host "Commande:" -ForegroundColor Cyan
Write-Host "  $prometheusExe" -ForegroundColor White
foreach ($arg in $arguments) {
    Write-Host "    $arg" -ForegroundColor Gray
}
Write-Host ""

# Demarrer Prometheus en arriere-plan
Write-Host "Demarrage de Prometheus..." -ForegroundColor Yellow
$process = Start-Process -FilePath $prometheusExe -ArgumentList $arguments -PassThru -NoNewWindow

Write-Host "Processus demarre (PID: $($process.Id))" -ForegroundColor Green
Write-Host "Attente de 10 secondes pour voir s'il demarre correctement..." -ForegroundColor Yellow

Start-Sleep -Seconds 10

if ($process.HasExited) {
    Write-Host "[ERREUR] Le processus s'est arrete (code: $($process.ExitCode))" -ForegroundColor Red
} else {
    Write-Host "[OK] Le processus fonctionne toujours" -ForegroundColor Green
    
    # Tester l'acces HTTP
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Prometheus repond sur le port $port" -ForegroundColor Green
        }
    } catch {
        Write-Host "[AVERTISSEMENT] Prometheus ne repond pas encore sur le port $port" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Arret du processus de test..." -ForegroundColor Yellow
    Stop-Process -Id $process.Id -Force
    Write-Host "[OK] Processus arrete" -ForegroundColor Green
}

Write-Host ""
Write-Host "Si Prometheus demarre correctement en manuel, le probleme est probablement:" -ForegroundColor Yellow
Write-Host "  1. Le service prend trop de temps a demarrer (timeout 30s)" -ForegroundColor White
Write-Host "  2. Il faut augmenter le timeout du service" -ForegroundColor White
Write-Host "  3. Ou utiliser NSSM qui gere mieux les services qui prennent du temps" -ForegroundColor White


