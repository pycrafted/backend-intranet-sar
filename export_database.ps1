# Script PowerShell pour exporter la base de données PostgreSQL
# Usage: .\export_database.ps1

# ============================================================================
# Configuration depuis .env
# ⚠️ SÉCURITÉ : Tous les paramètres DOIVENT être définis dans le fichier .env
# ============================================================================
# Fonction pour charger les variables depuis .env
function Load-EnvFile {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        Get-Content $FilePath | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Variable -Name $name -Value $value -Scope Script
            }
        }
    } else {
        Write-Host "❌ Erreur : Le fichier .env n'existe pas : $FilePath" -ForegroundColor Red
        Write-Host "💡 Créez un fichier .env avec les variables POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD" -ForegroundColor Yellow
        exit 1
    }
}

# Charger le fichier .env depuis le répertoire du script
$envFile = Join-Path $PSScriptRoot ".env"
Load-EnvFile -FilePath $envFile

# Vérifier que toutes les variables sont définies
$requiredVars = @('POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_DB', 'POSTGRES_PASSWORD')
foreach ($var in $requiredVars) {
    if (-not (Get-Variable -Name $var -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Erreur : La variable $var n'est pas définie dans .env" -ForegroundColor Red
        exit 1
    }
}

# Assigner aux variables utilisées dans le script
$DB_HOST = $POSTGRES_HOST
$DB_PORT = $POSTGRES_PORT
$DB_USER = $POSTGRES_USER
$DB_NAME = $POSTGRES_DB
$DB_PASSWORD = $POSTGRES_PASSWORD

# Dossier de backup (créé dans le dossier du projet)
$BACKUP_DIR = Join-Path $PSScriptRoot "backups"

# Créer le dossier de backup s'il n'existe pas
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    Write-Host "📁 Dossier de backup créé : $BACKUP_DIR" -ForegroundColor Cyan
}

# Nom du fichier avec timestamp
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = Join-Path $BACKUP_DIR "backup_sar_$TIMESTAMP.sql"

# Vérifier que pg_dump est disponible
$pgDumpPath = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDumpPath) {
    Write-Host "❌ Erreur : pg_dump n'est pas trouvé dans le PATH" -ForegroundColor Red
    Write-Host "💡 Assurez-vous que PostgreSQL est installé et que pg_dump est dans votre PATH" -ForegroundColor Yellow
    Write-Host "💡 Chemin typique : C:\Program Files\PostgreSQL\XX\bin\pg_dump.exe" -ForegroundColor Yellow
    exit 1
}

# Définir le mot de passe
$env:PGPASSWORD = $DB_PASSWORD

Write-Host ""
Write-Host "🔄 Export de la base de données en cours..." -ForegroundColor Yellow
Write-Host "   Base de données : $DB_NAME" -ForegroundColor Gray
Write-Host "   Serveur : $DB_HOST:$DB_PORT" -ForegroundColor Gray
Write-Host "   Utilisateur : $DB_USER" -ForegroundColor Gray
Write-Host ""

# Export avec options recommandées
& pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
    -F p `
    --clean `
    --if-exists `
    --no-owner `
    --no-privileges `
    --verbose `
    -f $BACKUP_FILE

# Vérifier le résultat
if ($LASTEXITCODE -eq 0) {
    $FILE_SIZE = (Get-Item $BACKUP_FILE).Length / 1MB
    Write-Host ""
    Write-Host "✅ Export réussi !" -ForegroundColor Green
    Write-Host "📁 Fichier : $BACKUP_FILE" -ForegroundColor Cyan
    Write-Host "📊 Taille : $([math]::Round($FILE_SIZE, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Pour importer sur une autre machine, utilisez :" -ForegroundColor Yellow
    Write-Host "   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f `"$BACKUP_FILE`"" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Erreur lors de l'export !" -ForegroundColor Red
    Write-Host "💡 Vérifiez :" -ForegroundColor Yellow
    Write-Host "   - Que PostgreSQL est en cours d'exécution" -ForegroundColor White
    Write-Host "   - Que les credentials sont corrects dans .env" -ForegroundColor White
    Write-Host "   - Que la base de données existe" -ForegroundColor White
    exit 1
}

# Nettoyer la variable d'environnement
Remove-Item Env:\PGPASSWORD

