# Script pour vérifier et corriger le fichier .env
# Ce script s'assure que le fichier .env est correctement formaté pour python-decouple

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Vérification du fichier .env" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $envFile)) {
    Write-Host "[ERREUR] Le fichier .env n'existe pas!" -ForegroundColor Red
    Write-Host "Exécutez: .\complete-env.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Fichier .env trouvé: $envFile" -ForegroundColor Green
Write-Host ""

# Lire le fichier ligne par ligne
$lines = Get-Content $envFile
$variables = @{}
$newContent = ""
$hasErrors = $false

Write-Host "Analyse du fichier..." -ForegroundColor Yellow
Write-Host ""

foreach ($line in $lines) {
    $originalLine = $line
    $trimmed = $line.Trim()
    
    # Ignorer les lignes vides
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        $newContent += "`n"
        continue
    }
    
    # Gérer les commentaires
    if ($trimmed.StartsWith('#')) {
        $newContent += "$line`n"
        continue
    }
    
    # Vérifier le format des variables
    if ($trimmed -match '^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$') {
        $varName = $matches[1]
        $varValue = $matches[2]
        
        # Nettoyer la valeur
        $varValue = $varValue.Trim()
        
        # Enlever les commentaires à la fin de la ligne
        if ($varValue -match '^(.+?)\s*#') {
            $varValue = $matches[1].Trim()
        }
        
        # Vérifier si la variable est vide (sauf pour celles qui peuvent l'être)
        $canBeEmpty = @("REDIS_PASSWORD", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL", 
                        "LDAP_SERVER", "LDAP_BIND_DN", "LDAP_BIND_PASSWORD")
        
        if ([string]::IsNullOrWhiteSpace($varValue) -and $canBeEmpty -notcontains $varName) {
            Write-Host "[ERREUR] Variable vide: $varName" -ForegroundColor Red
            $hasErrors = $true
        }
        
        # Vérifier les doublons
        if ($variables.ContainsKey($varName)) {
            Write-Host "[WARNING] Variable dupliquée: $varName (la première sera utilisée)" -ForegroundColor Yellow
        } else {
            $variables[$varName] = $varValue
            Write-Host "[OK] $varName = $($if($varValue.Length -gt 50){$varValue.Substring(0,50)+'...'}else{$varValue})" -ForegroundColor Green
        }
        
        # Réécrire la ligne proprement
        $newContent += "$varName=$varValue`n"
    } else {
        Write-Host "[WARNING] Ligne mal formatée ignorée: $trimmed" -ForegroundColor Yellow
        # Ne pas ajouter les lignes mal formatées
    }
}

# Vérifier les variables critiques
Write-Host ""
Write-Host "Vérification des variables critiques..." -ForegroundColor Yellow

$criticalVars = @{
    "POSTGRES_DB" = "intranet"
    "POSTGRES_USER" = "sar_user"
    "POSTGRES_PASSWORD" = "sar123"
    "POSTGRES_HOST" = "10.113.255.71"
    "POSTGRES_PORT" = "5432"
    "REDIS_HOST" = "sar-intranet.sar.sn"
    "REDIS_PORT" = "6379"
    "REDIS_DB" = "0"
    "SECRET_KEY" = ""
    "DEBUG" = "True"
    "ALLOWED_HOSTS" = ""
    "BASE_URL" = ""
    "FRONTEND_URL" = ""
}

$missingVars = @()
foreach ($varName in $criticalVars.Keys) {
    if (-not $variables.ContainsKey($varName)) {
        $missingVars += $varName
        Write-Host "[ERREUR] Variable manquante: $varName" -ForegroundColor Red
        $hasErrors = $true
        
        # Ajouter avec une valeur par défaut si disponible
        $defaultValue = $criticalVars[$varName]
        if (-not [string]::IsNullOrEmpty($defaultValue)) {
            $newContent += "$varName=$defaultValue`n"
            $variables[$varName] = $defaultValue
            Write-Host "  [AJOUTÉ] $varName = $defaultValue" -ForegroundColor Green
        }
    }
}

# Créer une sauvegarde
$backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $envFile $backupFile
Write-Host ""
Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green

# Écrire le nouveau contenu (sans BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($envFile, $newContent, $utf8NoBom)

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host "Vérification terminée avec des erreurs!" -ForegroundColor Yellow
    Write-Host "Le fichier a été corrigé automatiquement." -ForegroundColor Yellow
} else {
    Write-Host "Vérification terminée - Tout est OK!" -ForegroundColor Green
}
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Afficher un résumé
Write-Host "Résumé:" -ForegroundColor Yellow
Write-Host "  Variables trouvées: $($variables.Count)" -ForegroundColor White
Write-Host "  Variables manquantes: $($missingVars.Count)" -ForegroundColor $(if($missingVars.Count -eq 0){"Green"}else{"Red"})
Write-Host ""

# Test rapide avec Python
Write-Host "Test de lecture avec Python..." -ForegroundColor Yellow
try {
    $testScript = @"
import os
from pathlib import Path
from decouple import config, AutoConfig

BASE_DIR = Path(__file__).resolve().parent
config = AutoConfig(search_path=BASE_DIR)

try:
    postgres_db = config('POSTGRES_DB')
    print(f'[OK] POSTGRES_DB = {postgres_db}')
    redis_host = config('REDIS_HOST')
    print(f'[OK] REDIS_HOST = {redis_host}')
    print('[OK] Le fichier .env peut être lu correctement!')
except Exception as e:
    print(f'[ERREUR] {e}')
"@
    
    $testFile = Join-Path $PSScriptRoot "test_env_read.py"
    $testScript | Out-File -FilePath $testFile -Encoding UTF8
    
    $result = python $testFile 2>&1
    Write-Host $result
    
    Remove-Item $testFile -ErrorAction SilentlyContinue
} catch {
    Write-Host "[INFO] Test Python non disponible" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Vous pouvez maintenant tester avec: python test_redis.py" -ForegroundColor Green
Write-Host ""

