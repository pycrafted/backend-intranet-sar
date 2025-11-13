# Script pour configurer Memurai pour accepter les connexions distantes en production
# Ce script configure Memurai pour écouter sur toutes les interfaces (0.0.0.0)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration Memurai pour Production" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Emplacements possibles du fichier de configuration Memurai
$possibleConfigPaths = @(
    "C:\Program Files\Memurai\memurai.conf",
    "C:\Program Files (x86)\Memurai\memurai.conf",
    "C:\ProgramData\Memurai\memurai.conf"
)

$configFile = $null
foreach ($path in $possibleConfigPaths) {
    if (Test-Path $path) {
        $configFile = $path
        Write-Host "[OK] Fichier de configuration trouvé: $configFile" -ForegroundColor Green
        break
    }
}

if (-not $configFile) {
    Write-Host "[ERREUR] Fichier de configuration Memurai non trouvé!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Emplacements vérifiés:" -ForegroundColor Yellow
    foreach ($path in $possibleConfigPaths) {
        Write-Host "  - $path" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Veuillez trouver manuellement le fichier memurai.conf et modifier la ligne 'bind' :" -ForegroundColor Yellow
    Write-Host "  bind 0.0.0.0" -ForegroundColor White
    exit 1
}

# Lire le contenu du fichier de configuration
Write-Host ""
Write-Host "Lecture de la configuration actuelle..." -ForegroundColor Yellow
$content = Get-Content $configFile -Raw

# Vérifier si bind est déjà configuré
if ($content -match '(?m)^\s*bind\s+0\.0\.0\.0\s*$') {
    Write-Host "[OK] Memurai est déjà configuré pour écouter sur toutes les interfaces (0.0.0.0)" -ForegroundColor Green
} elseif ($content -match '(?m)^\s*bind\s+127\.0\.0\.1\s*$') {
    Write-Host "[INFO] Memurai écoute actuellement uniquement sur localhost (127.0.0.1)" -ForegroundColor Yellow
    Write-Host "Modification pour écouter sur toutes les interfaces..." -ForegroundColor Yellow
    
    # Remplacer bind 127.0.0.1 par bind 0.0.0.0
    $content = $content -replace '(?m)^(\s*)bind\s+127\.0\.0\.1\s*$', '$1bind 0.0.0.0'
    
    # Sauvegarder le fichier original
    $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $configFile $backupFile
    Write-Host "[OK] Sauvegarde créée: $backupFile" -ForegroundColor Green
    
    # Écrire la nouvelle configuration
    $content | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
    Write-Host "[OK] Configuration mise à jour: bind 0.0.0.0" -ForegroundColor Green
} elseif ($content -match '(?m)^\s*bind\s+') {
    Write-Host "[WARNING] Une configuration 'bind' existe mais n'est ni 127.0.0.1 ni 0.0.0.0" -ForegroundColor Yellow
    $currentBind = ($content | Select-String -Pattern '(?m)^\s*bind\s+(\S+)' | ForEach-Object { $_.Matches.Groups[1].Value })
    Write-Host "  Configuration actuelle: bind $currentBind" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Voulez-vous la remplacer par 'bind 0.0.0.0'? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        $content = $content -replace '(?m)^(\s*)bind\s+\S+\s*$', '$1bind 0.0.0.0'
        $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $configFile $backupFile
        $content | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
        Write-Host "[OK] Configuration mise à jour: bind 0.0.0.0" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Configuration non modifiée" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Aucune directive 'bind' trouvée. Ajout de 'bind 0.0.0.0'..." -ForegroundColor Yellow
    
    # Ajouter bind 0.0.0.0 après les commentaires de début ou au début du fichier
    if ($content -match '(?m)^(\s*#.*\n)*') {
        $content = $content -replace '((?m)^\s*#.*\n)*', "`$0bind 0.0.0.0`n"
    } else {
        $content = "bind 0.0.0.0`n" + $content
    }
    
    $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $configFile $backupFile
    $content | Out-File -FilePath $configFile -Encoding UTF8 -NoNewline
    Write-Host "[OK] Directive 'bind 0.0.0.0' ajoutée" -ForegroundColor Green
}

# Configurer le firewall
Write-Host ""
Write-Host "Configuration du firewall Windows..." -ForegroundColor Yellow

$firewallRule = Get-NetFirewallRule -DisplayName "Redis Server" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "[OK] Règle de firewall 'Redis Server' existe déjà" -ForegroundColor Green
} else {
    try {
        New-NetFirewallRule -DisplayName "Redis Server" `
            -Direction Inbound `
            -LocalPort 6379 `
            -Protocol TCP `
            -Action Allow `
            -Description "Autorise les connexions Redis entrantes pour la production" `
            -ErrorAction Stop
        Write-Host "[OK] Règle de firewall créée pour le port 6379" -ForegroundColor Green
    } catch {
        Write-Host "[ERREUR] Impossible de créer la règle de firewall: $_" -ForegroundColor Red
        Write-Host "Vous pouvez la créer manuellement avec:" -ForegroundColor Yellow
        Write-Host "  New-NetFirewallRule -DisplayName 'Redis Server' -Direction Inbound -LocalPort 6379 -Protocol TCP -Action Allow" -ForegroundColor White
    }
}

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
} else {
    Write-Host "[WARNING] Service Memurai non trouvé" -ForegroundColor Yellow
}

# Vérifier que Redis écoute sur toutes les interfaces
Write-Host ""
Write-Host "Vérification de la configuration..." -ForegroundColor Yellow

Start-Sleep -Seconds 2
$listening = netstat -an | Select-String ":6379" | Select-String "LISTENING"

if ($listening -match "0\.0\.0\.0:6379") {
    Write-Host "[OK] Redis écoute sur toutes les interfaces (0.0.0.0:6379)" -ForegroundColor Green
} elseif ($listening -match "127\.0\.0\.1:6379") {
    Write-Host "[WARNING] Redis écoute toujours uniquement sur localhost (127.0.0.1:6379)" -ForegroundColor Yellow
    Write-Host "  Le service peut nécessiter un redémarrage manuel" -ForegroundColor White
} else {
    Write-Host "[INFO] État de l'écoute Redis:" -ForegroundColor Yellow
    foreach ($line in $listening) {
        Write-Host "  $line" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Testez la connexion avec: python test_redis.py" -ForegroundColor White
Write-Host "  2. Depuis une autre machine, testez: redis-cli -h 10.113.255.71 ping" -ForegroundColor White
Write-Host "  3. Vérifiez les logs si nécessaire" -ForegroundColor White
Write-Host ""

