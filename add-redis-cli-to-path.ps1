# Script pour ajouter redis-cli au PATH Windows
# Ce script doit être exécuté en tant qu'administrateur

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Ajout de redis-cli au PATH Windows" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Emplacements possibles où Memurai installe redis-cli
$possiblePaths = @(
    "C:\Program Files\Memurai",
    "C:\Program Files (x86)\Memurai",
    "C:\ProgramData\chocolatey\lib\memurai-developer\tools",
    "C:\ProgramData\chocolatey\bin"
)

Write-Host "Recherche de redis-cli..." -ForegroundColor Yellow

$redisCliPath = $null
$redisCliFound = $false

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        Write-Host "  Vérification: $path" -ForegroundColor Gray
        
        # Chercher redis-cli.exe dans ce dossier et ses sous-dossiers
        $found = Get-ChildItem -Path $path -Filter "redis-cli.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        
        if ($found) {
            $redisCliPath = $found.DirectoryName
            $redisCliFound = $true
            Write-Host "  [OK] redis-cli trouvé dans: $redisCliPath" -ForegroundColor Green
            break
        }
    }
}

# Si pas trouvé, chercher dans tout le système
if (-not $redisCliFound) {
    Write-Host "  Recherche dans tout le système (cela peut prendre du temps)..." -ForegroundColor Yellow
    $found = Get-ChildItem -Path "C:\" -Filter "redis-cli.exe" -Recurse -ErrorAction SilentlyContinue -Depth 3 | Select-Object -First 1
    
    if ($found) {
        $redisCliPath = $found.DirectoryName
        $redisCliFound = $true
        Write-Host "  [OK] redis-cli trouvé dans: $redisCliPath" -ForegroundColor Green
    }
}

if (-not $redisCliFound) {
    Write-Host ""
    Write-Host "[ERREUR] redis-cli.exe n'a pas été trouvé!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions possibles:" -ForegroundColor Yellow
    Write-Host "1. Redémarrez votre terminal PowerShell (les variables PATH peuvent avoir changé)" -ForegroundColor White
    Write-Host "2. Exécutez: refreshenv" -ForegroundColor White
    Write-Host "3. Vérifiez manuellement dans: C:\Program Files\Memurai" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Vérifier si le chemin est déjà dans le PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$pathEntries = $currentPath -split ';'

if ($pathEntries -contains $redisCliPath) {
    Write-Host ""
    Write-Host "[INFO] Le chemin est déjà dans le PATH système" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Ajout du chemin au PATH système..." -ForegroundColor Yellow
    
    # Ajouter au PATH système (Machine)
    $newPath = $currentPath
    if (-not $newPath.EndsWith(';')) {
        $newPath += ';'
    }
    $newPath += $redisCliPath
    
    try {
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Host "[OK] Chemin ajouté au PATH système" -ForegroundColor Green
        
        # Mettre à jour le PATH de la session actuelle
        $env:Path += ";$redisCliPath"
        Write-Host "[OK] PATH de la session actuelle mis à jour" -ForegroundColor Green
    } catch {
        Write-Host "[ERREUR] Impossible d'ajouter au PATH: $_" -ForegroundColor Red
        exit 1
    }
}

# Vérifier que redis-cli fonctionne maintenant
Write-Host ""
Write-Host "Vérification de redis-cli..." -ForegroundColor Yellow

# Attendre un peu pour que les changements prennent effet
Start-Sleep -Seconds 1

try {
    $redisCli = Get-Command redis-cli -ErrorAction Stop
    Write-Host "[OK] redis-cli est maintenant disponible!" -ForegroundColor Green
    Write-Host "  Emplacement: $($redisCli.Source)" -ForegroundColor White
    
    # Tester la connexion
    Write-Host ""
    Write-Host "Test de connexion Redis..." -ForegroundColor Yellow
    $pingResult = redis-cli ping 2>&1
    if ($pingResult -eq "PONG") {
        Write-Host "[OK] Connexion Redis réussie! (PONG)" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Redis répond: $pingResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] redis-cli n'est pas encore disponible dans cette session" -ForegroundColor Yellow
    Write-Host "  Fermez et rouvrez votre terminal PowerShell pour que les changements prennent effet" -ForegroundColor White
    Write-Host "  Ou exécutez: refreshenv" -ForegroundColor White
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  Fermez et rouvrez votre terminal PowerShell pour que redis-cli soit disponible" -ForegroundColor White
Write-Host "  Ou exécutez: refreshenv" -ForegroundColor White
Write-Host ""

