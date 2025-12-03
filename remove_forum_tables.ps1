# ============================================================================
# Script PowerShell pour exécuter le script SQL de suppression du forum
# ============================================================================
# Ce script exécute le fichier SQL remove_forum_tables.sql sur la base de données
# ============================================================================

# Charger les variables d'environnement depuis .env si elles existent
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)\s*$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Récupérer les paramètres de connexion depuis les variables d'environnement
$dbName = $env:POSTGRES_DB
$dbUser = $env:POSTGRES_USER
$dbPassword = $env:POSTGRES_PASSWORD
$dbHost = $env:POSTGRES_HOST
$dbPort = $env:POSTGRES_PORT

# Vérifier que les variables sont définies
if (-not $dbName -or -not $dbUser -or -not $dbPassword -or -not $dbHost) {
    Write-Host "❌ Erreur : Les variables d'environnement de la base de données ne sont pas définies." -ForegroundColor Red
    Write-Host "   Assurez-vous que POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD et POSTGRES_HOST sont définies." -ForegroundColor Yellow
    exit 1
}

# Chemin vers le script SQL
$sqlScript = Join-Path $PSScriptRoot "remove_forum_tables.sql"

if (-not (Test-Path $sqlScript)) {
    Write-Host "❌ Erreur : Le fichier SQL $sqlScript n'existe pas." -ForegroundColor Red
    exit 1
}

Write-Host "⚠️  ATTENTION : Cette opération va supprimer définitivement toutes les données du forum !" -ForegroundColor Yellow
Write-Host ""
Write-Host "Base de données : $dbName" -ForegroundColor Cyan
Write-Host "Hôte : $dbHost" -ForegroundColor Cyan
Write-Host "Port : $dbPort" -ForegroundColor Cyan
Write-Host "Utilisateur : $dbUser" -ForegroundColor Cyan
Write-Host ""
$confirmation = Read-Host "Voulez-vous continuer ? (tapez 'OUI' pour confirmer)"

if ($confirmation -ne "OUI") {
    Write-Host "❌ Opération annulée." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🔄 Exécution du script SQL..." -ForegroundColor Cyan

# Construire la chaîne de connexion PostgreSQL
$env:PGPASSWORD = $dbPassword
$psqlCommand = "psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f `"$sqlScript`""

try {
    # Exécuter le script SQL avec psql
    Invoke-Expression $psqlCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Script SQL exécuté avec succès !" -ForegroundColor Green
        Write-Host "   Les tables du forum ont été supprimées de la base de données." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Erreur lors de l'exécution du script SQL (code de sortie: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "   Vérifiez que psql est installé et accessible dans votre PATH." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Erreur lors de l'exécution : $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative : Vous pouvez exécuter le script SQL manuellement avec :" -ForegroundColor Yellow
    Write-Host "   psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f `"$sqlScript`"" -ForegroundColor Cyan
    exit 1
} finally {
    # Nettoyer la variable d'environnement du mot de passe
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Host ""


