# Script pour configurer Redis avec l'adresse IP du serveur en production
# Ce script détecte automatiquement l'adresse IP ou permet de la spécifier manuellement

param(
    [string]$RedisHost = "",
    [int]$RedisPort = 6379,
    [int]$RedisDb = 0,
    [string]$RedisPassword = ""
)

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration Redis pour Production" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Si aucune adresse IP n'est fournie, détecter automatiquement
if ([string]::IsNullOrEmpty($RedisHost)) {
    Write-Host "Détection automatique de l'adresse IP du serveur..." -ForegroundColor Yellow
    
    # Obtenir toutes les adresses IP de la machine
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -ne "127.0.0.1" -and 
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown"
    } | Sort-Object -Property IPAddress
    
    if ($networkAdapters.Count -eq 0) {
        Write-Host "[ERREUR] Aucune adresse IP valide trouvée!" -ForegroundColor Red
        Write-Host "Veuillez spécifier manuellement l'adresse IP avec: -RedisHost <IP>" -ForegroundColor Yellow
        exit 1
    }
    
    if ($networkAdapters.Count -eq 1) {
        $RedisHost = $networkAdapters[0].IPAddress
        $interface = Get-NetAdapter -InterfaceIndex $networkAdapters[0].InterfaceIndex -ErrorAction SilentlyContinue
        $interfaceName = if ($interface) { $interface.Name } else { "Interface $($networkAdapters[0].InterfaceIndex)" }
        Write-Host "[OK] Une seule adresse IP trouvée: $RedisHost ($interfaceName)" -ForegroundColor Green
        Write-Host "[OK] Utilisation automatique de cette adresse IP" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Plusieurs adresses IP trouvées:" -ForegroundColor Yellow
        $index = 1
        $adapters = @()
        foreach ($adapter in $networkAdapters) {
            $interface = Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
            $interfaceName = if ($interface) { $interface.Name } else { "Interface $($adapter.InterfaceIndex)" }
            Write-Host "  $index. $($adapter.IPAddress) - $interfaceName" -ForegroundColor White
            $adapters += $adapter
            $index++
        }
        Write-Host ""
        
        $validChoice = $false
        $maxAttempts = 3
        $attempt = 0
        
        while (-not $validChoice -and $attempt -lt $maxAttempts) {
            $choice = Read-Host "Sélectionnez l'adresse IP à utiliser (1-$($adapters.Count))"
            
            # Nettoyer la saisie : extraire seulement le premier nombre
            $choice = $choice.Trim()
            if ($choice -match '^(\d+)') {
                $choice = $matches[1]
            }
            
            try {
                $selectedIndex = [int]$choice - 1
                if ($selectedIndex -ge 0 -and $selectedIndex -lt $adapters.Count) {
                    $RedisHost = $adapters[$selectedIndex].IPAddress
                    $interface = Get-NetAdapter -InterfaceIndex $adapters[$selectedIndex].InterfaceIndex -ErrorAction SilentlyContinue
                    $interfaceName = if ($interface) { $interface.Name } else { "Interface $($adapters[$selectedIndex].InterfaceIndex)" }
                    Write-Host "[OK] Adresse IP sélectionnée: $RedisHost ($interfaceName)" -ForegroundColor Green
                    $validChoice = $true
                } else {
                    $attempt++
                    Write-Host "[ERREUR] Veuillez entrer un nombre entre 1 et $($adapters.Count)" -ForegroundColor Red
                    if ($attempt -lt $maxAttempts) {
                        Write-Host "Tentative $attempt/$maxAttempts" -ForegroundColor Yellow
                    }
                }
            } catch {
                $attempt++
                Write-Host "[ERREUR] Veuillez entrer un nombre valide (1-$($adapters.Count))" -ForegroundColor Red
                if ($attempt -lt $maxAttempts) {
                    Write-Host "Tentative $attempt/$maxAttempts" -ForegroundColor Yellow
                }
            }
        }
        
        if (-not $validChoice) {
            Write-Host "[ERREUR] Trop de tentatives échouées. Arrêt du script." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "Utilisation de l'adresse IP fournie: $RedisHost" -ForegroundColor Green
}

# Vérifier si .env existe
if (-not (Test-Path $envFile)) {
    Write-Host ""
    Write-Host "[INFO] Le fichier .env n'existe pas. Création..." -ForegroundColor Yellow
    $envExampleFile = Join-Path $PSScriptRoot ".env.example"
    if (Test-Path $envExampleFile) {
        Copy-Item $envExampleFile $envFile
        Write-Host "[OK] Fichier .env créé depuis .env.example" -ForegroundColor Green
    } else {
        # Créer un fichier .env minimal
        @"
# Configuration Redis Production
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

Write-Host ""
Write-Host "Mise à jour des paramètres Redis pour la production..." -ForegroundColor Yellow

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
Write-Host "Paramètres Redis configurés pour la production:" -ForegroundColor Yellow
Write-Host "  REDIS_HOST=$RedisHost" -ForegroundColor White
Write-Host "  REDIS_PORT=$RedisPort" -ForegroundColor White
Write-Host "  REDIS_DB=$RedisDb" -ForegroundColor White
$passwordDisplay = if ($RedisPassword) { '***' } else { '<vide>' }
Write-Host "  REDIS_PASSWORD=$passwordDisplay" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT pour la production:" -ForegroundColor Yellow
Write-Host "  1. Vérifiez que Redis écoute sur toutes les interfaces (0.0.0.0) et non seulement localhost" -ForegroundColor White
Write-Host "  2. Configurez le firewall pour autoriser les connexions sur le port $RedisPort" -ForegroundColor White
Write-Host "  3. Si vous utilisez un mot de passe, configurez-le dans Redis et dans .env" -ForegroundColor White
Write-Host "  4. Testez la connexion avec: python test_redis.py" -ForegroundColor White
Write-Host ""

