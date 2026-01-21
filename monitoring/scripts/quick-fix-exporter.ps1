# Correction rapide du service Windows Exporter (sans le collector 'cs')
# Usage: .\quick-fix-exporter.ps1

$serviceName = "windows_exporter"
$exporterPath = "C:\Program Files\windows_exporter\windows_exporter.exe"
$arguments = "--web.listen-address=0.0.0.0:9182 --collectors.enabled=cpu,logical_disk,memory,net,os,process,system,textfile"

Write-Host "Correction du service Windows Exporter..." -ForegroundColor Yellow

# Arrêter et supprimer
Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
sc.exe delete $serviceName 2>&1 | Out-Null
Start-Sleep -Seconds 2

# Recréer
New-Service -Name $serviceName `
    -BinaryPathName "`"$exporterPath`" $arguments" `
    -DisplayName "Windows Exporter" `
    -StartupType Automatic `
    -Description "Prometheus exporter for Windows machines" | Out-Null

# Démarrer
Start-Service -Name $serviceName
Start-Sleep -Seconds 3

# Vérifier
$service = Get-Service -Name $serviceName
if ($service.Status -eq "Running") {
    Write-Host "[OK] Service démarré avec succès!" -ForegroundColor Green
    Write-Host "  Accès: http://sar-intranet.sar.sn:9182/metrics" -ForegroundColor Cyan
} else {
    Write-Host "[ERREUR] Service toujours arrêté" -ForegroundColor Red
    Get-EventLog -LogName Application -Source $serviceName -Newest 1 | Format-List
}











