# Script pour corriger le fichier de configuration Memurai
# Ce script supprime le BOM UTF-8 et corrige la syntaxe

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction du fichier de configuration Memurai" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

$configFile = "C:\Program Files\Memurai\memurai.conf"

if (-not (Test-Path $configFile)) {
    Write-Host "[ERREUR] Fichier de configuration non trouvé: $configFile" -ForegroundColor Red
    exit 1
}

# Créer une sauvegarde
$backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $configFile $backupFile
Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green

Write-Host ""
Write-Host "Lecture et correction du fichier..." -ForegroundColor Yellow

# Lire le fichier en tant qu'octets pour supprimer le BOM
$bytes = [System.IO.File]::ReadAllBytes($configFile)

# Supprimer le BOM UTF-8 (EF BB BF)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    Write-Host "[INFO] BOM UTF-8 détecté et supprimé" -ForegroundColor Yellow
    $bytes = $bytes[3..($bytes.Length-1)]
}

# Convertir en texte
$encoding = New-Object System.Text.UTF8Encoding $false
$content = $encoding.GetString($bytes)

# Extraire le mot de passe Redis si il existe
$redisPassword = ""
if ($content -match '(?m)^\s*requirepass\s+(.+)$') {
    $redisPassword = $matches[1].Trim()
    Write-Host "[OK] Mot de passe Redis trouvé dans la configuration" -ForegroundColor Green
}

# Lire le fichier original ligne par ligne pour reconstruire proprement
$lines = $content -split "`r?`n"
$newContent = ""
$requirepassAdded = $false

foreach ($line in $lines) {
    $trimmed = $line.Trim()
    
    # Ignorer les lignes vides
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        continue
    }
    
    # Ignorer les lignes qui commencent par # (commentaires)
    if ($trimmed.StartsWith('#')) {
        $newContent += "$line`n"
        continue
    }
    
    # Vérifier si c'est la directive requirepass
    if ($trimmed -match '^\s*requirepass\s+(.+)$') {
        $requirepassAdded = $true
        $newContent += "requirepass $redisPassword`n"
        continue
    }
    
    # Vérifier si c'est la directive bind
    if ($trimmed -match '^\s*bind\s+') {
        $newContent += "$line`n"
        continue
    }
    
    # Ajouter toutes les autres lignes valides
    if ($trimmed -match '^\s*[a-zA-Z]') {
        $newContent += "$line`n"
    }
}

# Si requirepass n'a pas été trouvé mais qu'on a un mot de passe, l'ajouter
if (-not $requirepassAdded -and -not [string]::IsNullOrEmpty($redisPassword)) {
    Write-Host "[INFO] Ajout de la directive requirepass..." -ForegroundColor Yellow
    # Ajouter après bind ou au début
    if ($newContent -match '(?m)^(bind\s+.*\n)') {
        $newContent = $newContent -replace '((?m)^bind\s+.*\n)', "`$1requirepass $redisPassword`n"
    } else {
        $newContent = "requirepass $redisPassword`n" + $newContent
    }
}

# Si on n'a pas de mot de passe, on peut continuer sans (optionnel)
if ([string]::IsNullOrEmpty($redisPassword)) {
    Write-Host "[WARNING] Aucun mot de passe Redis trouvé. Redis fonctionnera sans mot de passe." -ForegroundColor Yellow
}

# Écrire le fichier sans BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($configFile, $newContent, $utf8NoBom)

Write-Host "[OK] Fichier de configuration corrigé" -ForegroundColor Green

# Vérifier la syntaxe en essayant de démarrer le service
Write-Host ""
Write-Host "Vérification de la syntaxe..." -ForegroundColor Yellow

# Arrêter le service s'il est en cours d'exécution
$service = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq "Running") {
    Write-Host "Arrêt du service..." -ForegroundColor Yellow
    Stop-Service -Name "Memurai" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Démarrer le service
Write-Host "Démarrage du service..." -ForegroundColor Yellow
try {
    Start-Service -Name "Memurai" -ErrorAction Stop
    Start-Sleep -Seconds 3
    
    $service = Get-Service -Name "Memurai"
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service Memurai démarré avec succès!" -ForegroundColor Green
        
        # Vérifier que Redis écoute
        Start-Sleep -Seconds 1
        $listening = netstat -an | Select-String ":6379" | Select-String "LISTENING"
        if ($listening) {
            Write-Host "[OK] Redis écoute sur le port 6379" -ForegroundColor Green
        }
    } else {
        Write-Host "[ERREUR] Le service n'a pas démarré. Statut: $($service.Status)" -ForegroundColor Red
        
        # Afficher les dernières erreurs
        Start-Sleep -Seconds 1
        $errors = Get-EventLog -LogName Application -Source "Memurai" -Newest 3 -ErrorAction SilentlyContinue
        if ($errors) {
            Write-Host ""
            Write-Host "Dernières erreurs:" -ForegroundColor Red
            foreach ($error in $errors) {
                Write-Host "  [$($error.TimeGenerated)] $($error.Message)" -ForegroundColor White
            }
        }
    }
} catch {
    Write-Host "[ERREUR] Impossible de démarrer le service: $_" -ForegroundColor Red
    
    # Afficher les dernières erreurs
    $errors = Get-EventLog -LogName Application -Source "Memurai" -Newest 3 -ErrorAction SilentlyContinue
    if ($errors) {
        Write-Host ""
        Write-Host "Dernières erreurs:" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  [$($error.TimeGenerated)] $($error.Message)" -ForegroundColor White
        }
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Correction terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

