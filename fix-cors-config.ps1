# Script pour corriger la configuration CORS dans le fichier .env
# Ce script met à jour CORS_ALLOWED_ORIGINS et CSRF_TRUSTED_ORIGINS avec la bonne URL du frontend

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction de la configuration CORS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $envFile)) {
    Write-Host "[ERREUR] Le fichier .env n'existe pas!" -ForegroundColor Red
    Write-Host "Exécutez d'abord: .\complete-env.ps1" -ForegroundColor Yellow
    exit 1
}

# Lire le fichier .env
$content = Get-Content $envFile -Raw

# Extraire FRONTEND_URL pour l'utiliser comme valeur par défaut
$frontendUrl = ""
if ($content -match '(?m)^\s*FRONTEND_URL\s*=\s*(.+)$') {
    $frontendUrl = $matches[1].Trim()
    Write-Host "[OK] FRONTEND_URL trouvé: $frontendUrl" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] FRONTEND_URL non trouvé dans .env" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Mise à jour de la configuration CORS..." -ForegroundColor Yellow

# Fonction pour mettre à jour ou ajouter une variable
function Update-EnvVariable {
    param(
        [string]$Name,
        [string]$Value,
        [ref]$Content
    )
    
    $pattern = "^$Name=.*$"
    $newLine = "$Name=$Value"
    
    if ($Content.Value -match "(?m)^$Name=.*$") {
        # Variable existe, la mettre à jour
        $Content.Value = $Content.Value -replace $pattern, $newLine
        Write-Host "  [OK] $Name mis à jour: $Value" -ForegroundColor Green
    } else {
        # Variable n'existe pas, l'ajouter
        if ($Content.Value -notmatch "`n$") {
            $Content.Value += "`n"
        }
        $Content.Value += "$newLine`n"
        Write-Host "  [OK] $Name ajouté: $Value" -ForegroundColor Green
    }
}

# Mettre à jour CORS_ALLOWED_ORIGINS
Update-EnvVariable -Name "CORS_ALLOWED_ORIGINS" -Value $frontendUrl -Content ([ref]$content)

# Mettre à jour CSRF_TRUSTED_ORIGINS
Update-EnvVariable -Name "CSRF_TRUSTED_ORIGINS" -Value $frontendUrl -Content ([ref]$content)

# Créer une sauvegarde
$backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $envFile $backupFile
Write-Host ""
Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green

# Écrire le contenu mis à jour
$content | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration CORS corrigée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration mise à jour:" -ForegroundColor Yellow
Write-Host "  CORS_ALLOWED_ORIGINS=$frontendUrl" -ForegroundColor White
Write-Host "  CSRF_TRUSTED_ORIGINS=$frontendUrl" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Redémarrez le serveur Django pour que les changements prennent effet!" -ForegroundColor Yellow
Write-Host "  Arrêtez le serveur (Ctrl+C) et relancez:" -ForegroundColor White
Write-Host "  python manage.py runserver 10.113.255.71:8001" -ForegroundColor Cyan
Write-Host ""

