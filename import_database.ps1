# Script PowerShell pour importer la base de données PostgreSQL
# Usage: .\import_database.ps1 -BackupFile "chemin\vers\backup.sql"

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

# Configuration depuis .env
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_USER = "sar_user"
$DB_NAME = "sar"
$DB_PASSWORD = "sar123"

# Vérifier que le fichier existe
if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Erreur : Le fichier de backup n'existe pas : $BackupFile" -ForegroundColor Red
    exit 1
}

# Vérifier que psql est disponible
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "❌ Erreur : psql n'est pas trouvé dans le PATH" -ForegroundColor Red
    Write-Host "💡 Assurez-vous que PostgreSQL est installé et que psql est dans votre PATH" -ForegroundColor Yellow
    Write-Host "💡 Chemin typique : C:\Program Files\PostgreSQL\XX\bin\psql.exe" -ForegroundColor Yellow
    exit 1
}

# Afficher un avertissement
Write-Host ""
Write-Host "⚠️  ATTENTION : Cette opération va écraser les données existantes !" -ForegroundColor Red
Write-Host "   Base de données : $DB_NAME" -ForegroundColor Yellow
Write-Host "   Fichier de backup : $BackupFile" -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Voulez-vous continuer ? (oui/non)"

if ($confirmation -ne "oui" -and $confirmation -ne "o" -and $confirmation -ne "yes" -and $confirmation -ne "y") {
    Write-Host "❌ Import annulé" -ForegroundColor Yellow
    exit 0
}

# Définir le mot de passe
$env:PGPASSWORD = $DB_PASSWORD

Write-Host ""
Write-Host "🔄 Import de la base de données en cours..." -ForegroundColor Yellow
Write-Host "   Base de données : $DB_NAME" -ForegroundColor Gray
Write-Host "   Serveur : $DB_HOST:$DB_PORT" -ForegroundColor Gray
Write-Host "   Utilisateur : $DB_USER" -ForegroundColor Gray
Write-Host "   Fichier : $BackupFile" -ForegroundColor Gray
Write-Host ""

# Import avec gestion des erreurs
& psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
    -f $BackupFile `
    -v ON_ERROR_STOP=1

# Vérifier le résultat
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Import réussi !" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Vérifiez les données avec :" -ForegroundColor Yellow
    Write-Host "   psql -U $DB_USER -d $DB_NAME -c `"SELECT COUNT(*) FROM annuaire_employee;`"" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Erreur lors de l'import !" -ForegroundColor Red
    Write-Host "💡 Vérifiez :" -ForegroundColor Yellow
    Write-Host "   - Que PostgreSQL est en cours d'exécution" -ForegroundColor White
    Write-Host "   - Que la base de données existe" -ForegroundColor White
    Write-Host "   - Que l'utilisateur a les permissions nécessaires" -ForegroundColor White
    Write-Host "   - Les messages d'erreur ci-dessus" -ForegroundColor White
    exit 1
}

# Nettoyer la variable d'environnement
Remove-Item Env:\PGPASSWORD

