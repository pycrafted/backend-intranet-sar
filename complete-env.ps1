# Script pour compléter le fichier .env avec toutes les variables nécessaires
# Ce script ajoute les variables manquantes sans écraser les valeurs existantes

$envFile = Join-Path $PSScriptRoot ".env"
$envExampleFile = Join-Path $PSScriptRoot ".env.example"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Complétion du fichier .env" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Variables requises avec leurs valeurs par défaut (pour développement)
$requiredVars = @{
    # Django de base
    "SECRET_KEY" = "django-insecure-sbgp`$-92156s&no3gayf7b46=aaif8e%+(z**n6nn1mt+5tl&)"
    "DEBUG" = "True"
    "ALLOWED_HOSTS" = "localhost,127.0.0.1,0.0.0.0"
    
    # URLs
    "BASE_URL" = "http://localhost:8000"
    "FRONTEND_URL" = "http://localhost:3000"
    
    # PostgreSQL
    "POSTGRES_DB" = "intranet_db"
    "POSTGRES_USER" = "postgres"
    "POSTGRES_PASSWORD" = "postgres"
    "POSTGRES_HOST" = "localhost"
    "POSTGRES_PORT" = "5432"
    
    # Redis (déjà configuré, mais on s'assure qu'elles existent)
    "REDIS_HOST" = "localhost"
    "REDIS_PORT" = "6379"
    "REDIS_DB" = "0"
    "REDIS_PASSWORD" = ""
    
    # Email (SMTP)
    "EMAIL_BACKEND" = "django.core.mail.backends.smtp.EmailBackend"
    "EMAIL_HOST" = "smtp.office365.com"
    "EMAIL_PORT" = "587"
    "EMAIL_USE_TLS" = "True"
    "EMAIL_HOST_USER" = ""
    "EMAIL_HOST_PASSWORD" = ""
    "DEFAULT_FROM_EMAIL" = ""
    
    # CORS
    "CORS_ALLOWED_ORIGINS" = "http://localhost:3000"
    "CSRF_TRUSTED_ORIGINS" = "http://localhost:3000"
    
    # LDAP
    "LDAP_ENABLED" = "True"
    "LDAP_SERVER" = ""
    "LDAP_PORT" = "389"
    "LDAP_BASE_DN" = "DC=sar,DC=sn"
    "LDAP_BIND_DN" = ""
    "LDAP_BIND_PASSWORD" = ""
}

# Lire le contenu actuel du fichier .env
$content = ""
if (Test-Path $envFile) {
    $content = Get-Content $envFile -Raw
    Write-Host "[OK] Fichier .env existant trouvé" -ForegroundColor Green
} else {
    Write-Host "[INFO] Création d'un nouveau fichier .env" -ForegroundColor Yellow
    $content = ""
}

# Fonction pour vérifier si une variable existe
function VariableExists {
    param([string]$varName, [string]$content)
    return $content -match "(?m)^\s*$varName\s*="
}

# Fonction pour obtenir la valeur d'une variable existante
function GetVariableValue {
    param([string]$varName, [string]$content)
    if ($content -match "(?m)^\s*$varName\s*=\s*(.+)$") {
        return $matches[1].Trim()
    }
    return $null
}

Write-Host ""
Write-Host "Vérification et ajout des variables manquantes..." -ForegroundColor Yellow
Write-Host ""

$addedCount = 0
$existingCount = 0
$updatedCount = 0

# Vérifier chaque variable requise
foreach ($varName in $requiredVars.Keys) {
    $defaultValue = $requiredVars[$varName]
    
    if (VariableExists -varName $varName -content $content) {
        $existingValue = GetVariableValue -varName $varName -content $content
        if ([string]::IsNullOrWhiteSpace($existingValue)) {
            # Variable existe mais est vide, on la met à jour avec la valeur par défaut
            $content = $content -replace "(?m)^(\s*$varName\s*=)\s*$", "`$1$defaultValue"
            Write-Host "  [MISE À JOUR] $varName (était vide)" -ForegroundColor Yellow
            $updatedCount++
        } else {
            Write-Host "  [OK] $varName = $existingValue" -ForegroundColor Gray
            $existingCount++
        }
    } else {
        # Variable n'existe pas, on l'ajoute
        if ($content -notmatch "`n$" -and $content -ne "") {
            $content += "`n"
        }
        
        # Ajouter un commentaire pour les sections
        $sectionComments = @{
            "SECRET_KEY" = "`n# ============================================================================`n# Configuration Django de base`n# ============================================================================`n"
            "BASE_URL" = "`n# ============================================================================`n# Configuration des URLs`n# ============================================================================`n"
            "POSTGRES_DB" = "`n# ============================================================================`n# Configuration Base de Données PostgreSQL`n# ============================================================================`n"
            "REDIS_HOST" = "`n# ============================================================================`n# Configuration Redis`n# ============================================================================`n"
            "EMAIL_BACKEND" = "`n# ============================================================================`n# Configuration Email (SMTP)`n# ============================================================================`n"
            "CORS_ALLOWED_ORIGINS" = "`n# ============================================================================`n# Configuration CORS`n# ============================================================================`n"
            "LDAP_ENABLED" = "`n# ============================================================================`n# Configuration LDAP`n# ============================================================================`n"
        }
        
        if ($sectionComments.ContainsKey($varName)) {
            $content += $sectionComments[$varName]
        }
        
        $content += "$varName=$defaultValue`n"
        Write-Host "  [AJOUTÉ] $varName = $defaultValue" -ForegroundColor Green
        $addedCount++
    }
}

# Écrire le contenu mis à jour
$content | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Complétion terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Résumé:" -ForegroundColor Yellow
Write-Host "  Variables existantes: $existingCount" -ForegroundColor White
Write-Host "  Variables ajoutées: $addedCount" -ForegroundColor Green
Write-Host "  Variables mises à jour: $updatedCount" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  Vérifiez et modifiez les valeurs dans .env selon votre environnement:" -ForegroundColor White
Write-Host "  - POSTGRES_* : Paramètres de votre base de données PostgreSQL" -ForegroundColor White
Write-Host "  - REDIS_HOST : Déjà configuré pour la production (10.113.255.71)" -ForegroundColor White
Write-Host "  - EMAIL_* : Paramètres de votre serveur SMTP" -ForegroundColor White
Write-Host "  - LDAP_* : Paramètres de votre serveur LDAP" -ForegroundColor White
Write-Host ""
Write-Host "Vous pouvez maintenant tester avec: python test_redis.py" -ForegroundColor Green
Write-Host ""

