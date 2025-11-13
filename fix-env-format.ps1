# Script pour corriger le formatage du fichier .env
# Ce script nettoie et reformate correctement le fichier .env

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction du formatage du fichier .env" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $envFile)) {
    Write-Host "[ERREUR] Le fichier .env n'existe pas!" -ForegroundColor Red
    exit 1
}

# Lire le fichier ligne par ligne
$lines = Get-Content $envFile
$newContent = ""
$inSection = $false

foreach ($line in $lines) {
    $trimmedLine = $line.Trim()
    
    # Ignorer les lignes vides
    if ([string]::IsNullOrWhiteSpace($trimmedLine)) {
        continue
    }
    
    # Gérer les commentaires de section
    if ($trimmedLine -match '^#\s*=+') {
        if ($inSection) {
            $newContent += "`n"
        }
        $newContent += "$trimmedLine`n"
        $inSection = $true
        continue
    }
    
    # Gérer les commentaires normaux
    if ($trimmedLine.StartsWith('#')) {
        $newContent += "$trimmedLine`n"
        continue
    }
    
    # Gérer les variables d'environnement
    if ($trimmedLine -match '^([^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        
        # Nettoyer la valeur si elle contient des commentaires mal placés
        if ($varValue -match '^#') {
            # La valeur est un commentaire, la variable est vide
            $varValue = ""
        } elseif ($varValue -match '(.+?)\s*#') {
            # La valeur contient un commentaire à la fin, extraire seulement la valeur
            $varValue = $matches[1].Trim()
        }
        
        # Écrire la variable proprement
        $newContent += "$varName=$varValue`n"
        continue
    }
    
    # Ligne non reconnue, l'ajouter telle quelle
    $newContent += "$trimmedLine`n"
}

# Créer une sauvegarde
$backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $envFile $backupFile
Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green

# Écrire le nouveau contenu
$newContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host "[OK] Fichier .env corrigé et reformaté" -ForegroundColor Green
Write-Host ""
Write-Host "Vérification des variables critiques..." -ForegroundColor Yellow

# Vérifier que les variables critiques existent
$criticalVars = @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", 
                   "REDIS_HOST", "REDIS_PORT", "REDIS_DB", "SECRET_KEY", "DEBUG", "ALLOWED_HOSTS",
                   "BASE_URL", "FRONTEND_URL")

$missingVars = @()
foreach ($var in $criticalVars) {
    if ($newContent -notmatch "(?m)^\s*$var\s*=") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "[ERREUR] Variables manquantes:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Exécutez: .\complete-env.ps1 pour les ajouter" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Toutes les variables critiques sont présentes" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

