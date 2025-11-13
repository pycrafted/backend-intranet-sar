# Script pour configurer un mot de passe Redis et corriger le fichier .env
# Ce script génère un mot de passe sécurisé, le configure dans Memurai et met à jour .env

param(
    [string]$RedisPassword = ""
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration du mot de passe Redis" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Générer un mot de passe si non fourni
if ([string]::IsNullOrEmpty($RedisPassword)) {
    Write-Host "Génération d'un mot de passe sécurisé..." -ForegroundColor Yellow
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    $password = ""
    for ($i = 0; $i -lt 32; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    Write-Host "[OK] Mot de passe généré" -ForegroundColor Green
} else {
    $password = $RedisPassword
    Write-Host "Utilisation du mot de passe fourni" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Mot de passe Redis: $password" -ForegroundColor Cyan
Write-Host ""

# Trouver le fichier de configuration Memurai
$configFile = "C:\Program Files\Memurai\memurai.conf"
if (-not (Test-Path $configFile)) {
    Write-Host "[ERREUR] Fichier de configuration Memurai non trouvé: $configFile" -ForegroundColor Red
    exit 1
}

Write-Host "Configuration de Memurai..." -ForegroundColor Yellow

# Lire le fichier de configuration
$content = Get-Content $configFile -Raw

# Vérifier si requirepass existe déjà
if ($content -match '(?m)^\s*requirepass\s+') {
    Write-Host "[INFO] Un mot de passe Redis existe déjà" -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous le remplacer? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        $content = $content -replace '(?m)^(\s*)requirepass\s+.*$', "`$1requirepass $password"
        Write-Host "[OK] Mot de passe Redis mis à jour dans la configuration" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Configuration non modifiée" -ForegroundColor Yellow
        # Extraire le mot de passe existant
        if ($content -match '(?m)^\s*requirepass\s+(.+)$') {
            $password = $matches[1].Trim()
            Write-Host "[INFO] Utilisation du mot de passe existant" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[INFO] Ajout de la directive requirepass..." -ForegroundColor Yellow
    # Ajouter requirepass après la section bind ou au début
    if ($content -match '(?m)^(\s*bind\s+.*\n)') {
        $content = $content -replace '((?m)^\s*bind\s+.*\n)', "`$1requirepass $password`n"
    } else {
        $content = "requirepass $password`n" + $content
    }
    Write-Host "[OK] Mot de passe Redis ajouté à la configuration" -ForegroundColor Green
}

# Créer une sauvegarde
$backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $configFile $backupFile
Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green

# Écrire la nouvelle configuration
$content | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline

# Mettre à jour le fichier .env
Write-Host ""
Write-Host "Mise à jour du fichier .env..." -ForegroundColor Yellow

$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[ERREUR] Le fichier .env n'existe pas!" -ForegroundColor Red
    Write-Host "Exécutez d'abord: .\complete-env.ps1" -ForegroundColor Yellow
    exit 1
}

# Lire le fichier .env
$envContent = Get-Content $envFile -Raw

# Corriger REDIS_PASSWORD
if ($envContent -match '(?m)^\s*REDIS_PASSWORD\s*=') {
    # Remplacer la ligne existante
    $envContent = $envContent -replace '(?m)^(\s*REDIS_PASSWORD\s*=).*$', "`$1$password"
    Write-Host "[OK] REDIS_PASSWORD mis à jour dans .env" -ForegroundColor Green
} else {
    # Ajouter REDIS_PASSWORD
    if ($envContent -notmatch "`n$") {
        $envContent += "`n"
    }
    $envContent += "REDIS_PASSWORD=$password`n"
    Write-Host "[OK] REDIS_PASSWORD ajouté dans .env" -ForegroundColor Green
}

# Corriger toutes les variables qui pourraient avoir des problèmes de formatage
# S'assurer que chaque variable est sur une seule ligne sans commentaires mal placés
$lines = $envContent -split "`n"
$newEnvContent = ""
$inComment = $false

foreach ($line in $lines) {
    $trimmed = $line.Trim()
    
    # Ignorer les lignes vides
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        $newEnvContent += "`n"
        continue
    }
    
    # Gérer les commentaires de section
    if ($trimmed -match '^#\s*=+') {
        $newEnvContent += "$line`n"
        continue
    }
    
    # Gérer les commentaires normaux
    if ($trimmed.StartsWith('#')) {
        $newEnvContent += "$line`n"
        continue
    }
    
    # Gérer les variables
    if ($trimmed -match '^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$') {
        $varName = $matches[1]
        $varValue = $matches[2]
        
        # Nettoyer la valeur : enlever les commentaires à la fin
        if ($varValue -match '^(.+?)\s*#') {
            $varValue = $matches[1].Trim()
        }
        
        # S'assurer que la valeur n'est pas vide si c'est une variable critique
        $criticalVars = @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT")
        if ($criticalVars -contains $varName -and [string]::IsNullOrWhiteSpace($varValue)) {
            Write-Host "[WARNING] Variable critique vide: $varName" -ForegroundColor Yellow
        }
        
        $newEnvContent += "$varName=$varValue`n"
        continue
    }
    
    # Ligne non reconnue, l'ajouter telle quelle
    $newEnvContent += "$line`n"
}

# Créer une sauvegarde du .env
$envBackup = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $envFile $envBackup
Write-Host "[OK] Sauvegarde .env créée: $envBackup" -ForegroundColor Green

# Écrire le nouveau contenu
$newEnvContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

# Redémarrer le service Memurai
Write-Host ""
Write-Host "Redémarrage du service Memurai..." -ForegroundColor Yellow

$memuraiService = Get-Service -Name "Memurai*" -ErrorAction SilentlyContinue
if ($memuraiService) {
    try {
        Restart-Service -Name $memuraiService.Name -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        if ((Get-Service -Name $memuraiService.Name).Status -eq "Running") {
            Write-Host "[OK] Service Memurai redémarré avec succès" -ForegroundColor Green
        } else {
            Write-Host "[ERREUR] Le service Memurai n'a pas démarré correctement" -ForegroundColor Red
        }
    } catch {
        Write-Host "[ERREUR] Impossible de redémarrer le service: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Mot de passe Redis configuré:" -ForegroundColor Yellow
Write-Host "  $password" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Notez ce mot de passe, il est nécessaire pour se connecter à Redis!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Vous pouvez maintenant tester avec: python test_redis.py" -ForegroundColor Green
Write-Host ""

