# Script pour corriger la configuration CORS dans le fichier .env
# Ce script ajoute BASE_URL, FRONTEND_URL et vérifie/corrige CORS_ALLOWED_ORIGINS

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction de la configuration CORS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $envFile)) {
    Write-Host "[ERREUR] Le fichier .env n'existe pas!" -ForegroundColor Red
    Write-Host "Exécutez: .\complete-env.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Fichier .env trouvé: $envFile" -ForegroundColor Green
Write-Host ""

# Lire le contenu actuel
$content = Get-Content $envFile -Raw

# Fonction pour mettre à jour ou ajouter une variable
function Update-EnvVariable {
    param(
        [string]$Name,
        [string]$Value,
        [ref]$ContentRef
    )
    
    $pattern = "(?m)^\s*$Name\s*=\s*.*$"
    if ($ContentRef.Value -match $pattern) {
        # Remplacer la variable existante
        $ContentRef.Value = $ContentRef.Value -replace $pattern, "$Name=$Value"
        Write-Host "  [MISE À JOUR] $Name=$Value" -ForegroundColor Yellow
    } else {
        # Ajouter la variable
        if ($ContentRef.Value -notmatch '\n\s*$') {
            $ContentRef.Value += "`n"
        }
        $ContentRef.Value += "$Name=$Value`n"
        Write-Host "  [AJOUT] $Name=$Value" -ForegroundColor Green
    }
}

# Déterminer les URLs à partir de CORS_ALLOWED_ORIGINS ou utiliser des valeurs par défaut
$baseUrl = "http://sar-intranet.sar.sn:8001"
$frontendUrl = "http://sar-intranet.sar.sn:3001"
$corsOrigins = "http://localhost:3001,http://sar-intranet.sar.sn:3001"
$csrfOrigins = "http://localhost:3001,http://sar-intranet.sar.sn:3001"

# Extraire BASE_URL s'il existe
if ($content -match '(?m)^\s*BASE_URL\s*=\s*(.+)$') {
    $baseUrl = $matches[1].Trim()
    Write-Host "[OK] BASE_URL trouvé: $baseUrl" -ForegroundColor Green
} else {
    Write-Host "[INFO] BASE_URL non trouvé, utilisation de: $baseUrl" -ForegroundColor Yellow
}

# Extraire FRONTEND_URL s'il existe
if ($content -match '(?m)^\s*FRONTEND_URL\s*=\s*(.+)$') {
    $frontendUrl = $matches[1].Trim()
    Write-Host "[OK] FRONTEND_URL trouvé: $frontendUrl" -ForegroundColor Green
} else {
    Write-Host "[INFO] FRONTEND_URL non trouvé, utilisation de: $frontendUrl" -ForegroundColor Yellow
}

# Extraire CORS_ALLOWED_ORIGINS s'il existe
if ($content -match '(?m)^\s*CORS_ALLOWED_ORIGINS\s*=\s*(.+)$') {
    $corsOrigins = $matches[1].Trim()
    Write-Host "[OK] CORS_ALLOWED_ORIGINS trouvé: $corsOrigins" -ForegroundColor Green
    
    # Nettoyer les espaces
    $corsOrigins = $corsOrigins -replace '\s+', ''
} else {
    Write-Host "[INFO] CORS_ALLOWED_ORIGINS non trouvé, utilisation de: $corsOrigins" -ForegroundColor Yellow
}

# Extraire CSRF_TRUSTED_ORIGINS s'il existe
if ($content -match '(?m)^\s*CSRF_TRUSTED_ORIGINS\s*=\s*(.+)$') {
    $csrfOrigins = $matches[1].Trim()
    Write-Host "[OK] CSRF_TRUSTED_ORIGINS trouvé: $csrfOrigins" -ForegroundColor Green
    
    # Nettoyer les espaces
    $csrfOrigins = $csrfOrigins -replace '\s+', ''
} else {
    Write-Host "[INFO] CSRF_TRUSTED_ORIGINS non trouvé, utilisation de: $csrfOrigins" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Mise à jour de la configuration..." -ForegroundColor Yellow
Write-Host ""

# Mettre à jour ou ajouter les variables
Update-EnvVariable -Name "BASE_URL" -Value $baseUrl -Content ([ref]$content)
Update-EnvVariable -Name "FRONTEND_URL" -Value $frontendUrl -Content ([ref]$content)
Update-EnvVariable -Name "CORS_ALLOWED_ORIGINS" -Value $corsOrigins -Content ([ref]$content)
Update-EnvVariable -Name "CSRF_TRUSTED_ORIGINS" -Value $csrfOrigins -Content ([ref]$content)

# Sauvegarder le fichier
$content | Set-Content $envFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration CORS corrigée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Variables configurées:" -ForegroundColor Yellow
Write-Host "  BASE_URL=$baseUrl" -ForegroundColor White
Write-Host "  FRONTEND_URL=$frontendUrl" -ForegroundColor White
Write-Host "  CORS_ALLOWED_ORIGINS=$corsOrigins" -ForegroundColor White
Write-Host "  CSRF_TRUSTED_ORIGINS=$csrfOrigins" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Redémarrez votre serveur Django pour appliquer les changements!" -ForegroundColor Yellow
Write-Host ""

