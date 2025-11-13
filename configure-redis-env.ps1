# Script pour configurer les variables d'environnement Redis dans le fichier .env
# Ce script ajoute ou met à jour les paramètres Redis dans votre fichier .env

param(
    [string]$RedisHost = "localhost",
    [int]$RedisPort = 6379,
    [int]$RedisDb = 0,
    [string]$RedisPassword = "",
    [switch]$Production = $false
)

$envFile = Join-Path $PSScriptRoot ".env"
$envExampleFile = Join-Path $PSScriptRoot ".env.example"

Write-Host "=========================================" -ForegroundColor Cyan
if ($Production) {
    Write-Host "Configuration Redis pour PRODUCTION" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[INFO] Mode production activé" -ForegroundColor Yellow
    Write-Host "Si RedisHost n'est pas spécifié, l'adresse IP du serveur sera détectée automatiquement" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "Configuration Redis dans .env (Développement)" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[INFO] Mode développement - utilise localhost par défaut" -ForegroundColor Yellow
    Write-Host "Pour la production, utilisez: .\configure-redis-production.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Vérifier si .env existe
if (-not (Test-Path $envFile)) {
    Write-Host "[INFO] Le fichier .env n'existe pas." -ForegroundColor Yellow
    
    if (Test-Path $envExampleFile) {
        Write-Host "[INFO] Copie de .env.example vers .env..." -ForegroundColor Yellow
        Copy-Item $envExampleFile $envFile
        Write-Host "[OK] Fichier .env créé depuis .env.example" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Création d'un nouveau fichier .env..." -ForegroundColor Yellow
        # Créer un fichier .env minimal
        @"
# Configuration Redis
REDIS_HOST=$RedisHost
REDIS_PORT=$RedisPort
REDIS_DB=$RedisDb
REDIS_PASSWORD=$RedisPassword
"@ | Out-File -FilePath $envFile -Encoding UTF8
        Write-Host "[OK] Fichier .env créé avec les paramètres Redis" -ForegroundColor Green
    }
}

# Lire le contenu actuel du fichier .env
$content = Get-Content $envFile -Raw

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
        Write-Host "  [OK] $Name mis à jour" -ForegroundColor Green
    } else {
        # Variable n'existe pas, l'ajouter
        if ($Content.Value -notmatch "`n$") {
            $Content.Value += "`n"
        }
        $Content.Value += "$newLine`n"
        Write-Host "  [OK] $Name ajouté" -ForegroundColor Green
    }
}

Write-Host "Mise à jour des paramètres Redis..." -ForegroundColor Yellow

# Mettre à jour les variables Redis
Update-EnvVariable -Name "REDIS_HOST" -Value $RedisHost -Content ([ref]$content)
Update-EnvVariable -Name "REDIS_PORT" -Value $RedisPort -Content ([ref]$content)
Update-EnvVariable -Name "REDIS_DB" -Value $RedisDb -Content ([ref]$content)

if ($RedisPassword) {
    Update-EnvVariable -Name "REDIS_PASSWORD" -Value $RedisPassword -Content ([ref]$content)
} else {
    # S'assurer que REDIS_PASSWORD existe même si vide
    if ($content -notmatch "(?m)^REDIS_PASSWORD=.*$") {
        if ($content -notmatch "`n$") {
            $content += "`n"
        }
        $content += "REDIS_PASSWORD=`n"
        Write-Host "  [OK] REDIS_PASSWORD ajouté (vide)" -ForegroundColor Green
    }
}

# Écrire le contenu mis à jour
$content | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Paramètres Redis configurés:" -ForegroundColor Yellow
Write-Host "  REDIS_HOST=$RedisHost" -ForegroundColor White
Write-Host "  REDIS_PORT=$RedisPort" -ForegroundColor White
Write-Host "  REDIS_DB=$RedisDb" -ForegroundColor White
$passwordDisplay = if ($RedisPassword) { '***' } else { '<vide>' }
Write-Host "  REDIS_PASSWORD=$passwordDisplay" -ForegroundColor White
Write-Host ""
Write-Host "Vous pouvez maintenant tester la connexion avec:" -ForegroundColor Yellow
Write-Host "  python test_redis.py" -ForegroundColor White
Write-Host ""

