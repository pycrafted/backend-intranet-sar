# Script d'installation de Windows Exporter pour Prometheus
# Windows Exporter expose les métriques système Windows (CPU, RAM, Disque)
# Usage: .\install-windows-exporter.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation de Windows Exporter" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Faites un clic droit sur PowerShell et sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
    exit 1
}

# Configuration
$installDir = "C:\Program Files\windows_exporter"
$serviceName = "windows_exporter"
$port = 9182
$exporterPath = Join-Path $installDir "windows_exporter.exe"

# Obtenir l'URL de téléchargement via l'API GitHub
Write-Host "[INFO] Recherche de la dernière version de Windows Exporter..." -ForegroundColor Yellow
try {
    $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/prometheus-community/windows_exporter/releases/latest" -UseBasicParsing
    $downloadUrl = ($releaseInfo.assets | Where-Object { $_.name -eq "windows_exporter-amd64.exe" }).browser_download_url
    
    if (-not $downloadUrl) {
        # Fallback : URL directe si l'API ne fonctionne pas
        $version = $releaseInfo.tag_name -replace '^v', ''
        $downloadUrl = "https://github.com/prometheus-community/windows_exporter/releases/download/v$version/windows_exporter-amd64.exe"
    }
    
    Write-Host "[OK] Version trouvée: $($releaseInfo.tag_name)" -ForegroundColor Green
    Write-Host "  URL: $downloadUrl" -ForegroundColor Gray
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de récupérer la version via l'API, utilisation d'une URL directe" -ForegroundColor Yellow
    # URL directe vers une version récente (fallback)
    $downloadUrl = "https://github.com/prometheus-community/windows_exporter/releases/download/v0.25.2/windows_exporter-amd64.exe"
}

# Vérifier si Windows Exporter est déjà installé
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Windows Exporter est déjà installé" -ForegroundColor Yellow
    Write-Host "  Service: $($existingService.DisplayName)" -ForegroundColor White
    Write-Host "  Statut: $($existingService.Status)" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Voulez-vous réinstaller? (O/N)"
    if ($response -ne 'O' -and $response -ne 'o') {
        Write-Host "[ANNULÉ] Installation annulée" -ForegroundColor Yellow
        exit 0
    }
    
    # Arrêter et supprimer le service existant
    Write-Host "Arrêt du service existant..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Supprimer le service
    $servicePath = (Get-WmiObject Win32_Service -Filter "Name='$serviceName'").PathName
    if ($servicePath) {
        $servicePath = $servicePath.Trim('"')
        sc.exe delete $serviceName | Out-Null
        Start-Sleep -Seconds 2
    }
}

# Créer le répertoire d'installation
Write-Host "[INFO] Création du répertoire d'installation: $installDir" -ForegroundColor Yellow
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Write-Host "[OK] Répertoire créé" -ForegroundColor Green
} else {
    Write-Host "[OK] Répertoire existe déjà" -ForegroundColor Green
}

# Vérifier si le fichier existe déjà (téléchargé manuellement)
$tempFile = Join-Path $env:TEMP "windows_exporter-amd64.exe"
$manualFiles = @(
    $tempFile,
    (Join-Path $env:USERPROFILE "Downloads\windows_exporter-*-amd64.exe"),
    (Join-Path $env:USERPROFILE "Downloads\windows_exporter-amd64.exe"),
    (Join-Path $env:USERPROFILE "Desktop\windows_exporter-*-amd64.exe"),
    (Join-Path $env:USERPROFILE "Desktop\windows_exporter-amd64.exe")
)

$existingFile = $null
foreach ($pattern in $manualFiles) {
    $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $existingFile = $found.FullName
        Write-Host "[INFO] Fichier Windows Exporter trouvé: $existingFile" -ForegroundColor Green
        break
    }
}

# Télécharger Windows Exporter si nécessaire
if (-not $existingFile) {
    Write-Host ""
    Write-Host "[INFO] Téléchargement de Windows Exporter..." -ForegroundColor Yellow
    Write-Host "  URL: $downloadUrl" -ForegroundColor Gray

    $maxRetries = 3
    $retryCount = 0
    $downloadSuccess = $false

    while ($retryCount -lt $maxRetries -and -not $downloadSuccess) {
    $retryCount++
    
    if ($retryCount -gt 1) {
        Write-Host "  Tentative $retryCount/$maxRetries..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
    
    try {
        # Supprimer le fichier temporaire s'il existe
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
        }
        
        # Utiliser Invoke-WebRequest avec timeout et retry
        Write-Host "  Téléchargement en cours..." -ForegroundColor Gray
        $ProgressPreference = 'SilentlyContinue'
        
        # Configuration pour le téléchargement
        $params = @{
            Uri = $downloadUrl
            OutFile = $tempFile
            UseBasicParsing = $true
            TimeoutSec = 300  # 5 minutes de timeout
            UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ErrorAction = 'Stop'
        }
        
        Invoke-WebRequest @params
        
        # Vérifier que le fichier a été téléchargé
        if (Test-Path $tempFile) {
            $fileInfo = Get-Item $tempFile
            
            # Vérifier la taille (doit être > 1 MB pour un exécutable)
            if ($fileInfo.Length -lt 1000000) {
                # Si le fichier est trop petit, vérifier si c'est du HTML
                $content = Get-Content $tempFile -Raw -ErrorAction SilentlyContinue -TotalCount 100
                if ($content -match "<!DOCTYPE html" -or $content -match "<html") {
                    throw "Le téléchargement a retourné une page HTML au lieu du fichier binaire"
                }
            }
            
            Write-Host "[OK] Téléchargement terminé ($([math]::Round($fileInfo.Length/1MB, 2)) MB)" -ForegroundColor Green
            $downloadSuccess = $true
        } else {
            throw "Le fichier n'a pas été téléchargé"
        }
    } catch {
        if ($retryCount -ge $maxRetries) {
            Write-Host "[ERREUR] Échec du téléchargement après $maxRetries tentatives" -ForegroundColor Red
            Write-Host "  Dernière erreur: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Solutions possibles:" -ForegroundColor Yellow
            Write-Host "  1. Vérifiez votre connexion Internet" -ForegroundColor White
            Write-Host "  2. Téléchargez manuellement depuis:" -ForegroundColor White
            Write-Host "     $downloadUrl" -ForegroundColor Cyan
            Write-Host "  3. Placez le fichier dans: $tempFile" -ForegroundColor White
            Write-Host "  4. Relancez le script" -ForegroundColor White
            exit 1
        } else {
            Write-Host "  [AVERTISSEMENT] Erreur: $_" -ForegroundColor Yellow
            Write-Host "  Nouvelle tentative dans 2 secondes..." -ForegroundColor Yellow
        }
    }
}

    if (-not $downloadSuccess) {
        Write-Host "[ERREUR] Impossible de télécharger Windows Exporter" -ForegroundColor Red
        exit 1
    }
    $existingFile = $tempFile
}

# Copier vers le répertoire d'installation
Write-Host ""
Write-Host "[INFO] Installation de Windows Exporter..." -ForegroundColor Yellow
Copy-Item -Path $existingFile -Destination $exporterPath -Force
Write-Host "[OK] Windows Exporter installé dans: $exporterPath" -ForegroundColor Green

# Nettoyer le fichier temporaire si c'était un téléchargement automatique
if ($existingFile -eq $tempFile) {
    Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
}

# Configurer les collectors (CPU, RAM, Disque, Processus)
# Écouter sur toutes les interfaces (0.0.0.0) pour permettre l'accès depuis sar-intranet.sar.sn
# Note: 'cs' n'existe pas dans la v0.31.3, utiliser les collectors valides
$collectors = "cpu,logical_disk,memory,net,os,process,system,textfile"
$arguments = "--web.listen-address=0.0.0.0:$port --collectors.enabled=$collectors"

# Créer le service Windows
Write-Host ""
Write-Host "[INFO] Création du service Windows..." -ForegroundColor Yellow

try {
    # Supprimer le service s'il existe déjà
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "  Arrêt du service existant..." -ForegroundColor Yellow
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        & sc.exe delete $serviceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }
    
    # Créer le nouveau service avec la syntaxe correcte de sc.exe
    # Le binPath doit être entre guillemets si le chemin contient des espaces
    # Format: "chemin\exe" arguments
    $binPathWithArgs = "`"$exporterPath`" $arguments"
    Write-Host "  Création du service avec binPath: $binPathWithArgs" -ForegroundColor Gray
    
    $result = & sc.exe create $serviceName binPath= $binPathWithArgs start= auto DisplayName= "Windows Exporter" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Service créé avec succès" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Échec de la création du service" -ForegroundColor Red
        Write-Host "  Code de sortie: $LASTEXITCODE" -ForegroundColor Gray
        Write-Host "  Résultat: $result" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Tentative alternative avec New-Service..." -ForegroundColor Yellow
        
        # Tentative alternative avec New-Service (PowerShell)
        try {
            $serviceParams = @{
                Name = $serviceName
                BinaryPathName = "$exporterPath $arguments"
                DisplayName = "Windows Exporter"
                StartupType = "Automatic"
                Description = "Prometheus exporter for Windows machines"
            }
            New-Service @serviceParams -ErrorAction Stop
            Write-Host "[OK] Service créé avec New-Service" -ForegroundColor Green
        } catch {
            Write-Host "[ERREUR] Échec avec New-Service: $_" -ForegroundColor Red
            exit 1
        }
    }
    
    # Configurer le service pour démarrer automatiquement
    Set-Service -Name $serviceName -StartupType Automatic -ErrorAction Stop
    Write-Host "[OK] Service configuré pour démarrer automatiquement" -ForegroundColor Green
    
    # Démarrer le service
    Write-Host "[INFO] Démarrage du service..." -ForegroundColor Yellow
    Start-Service -Name $serviceName -ErrorAction Stop
    Start-Sleep -Seconds 3
    
    $service = Get-Service -Name $serviceName
    if ($service.Status -eq "Running") {
        Write-Host "[OK] Service démarré avec succès" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Le service n'a pas démarré. Statut: $($service.Status)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Diagnostic des erreurs..." -ForegroundColor Yellow
        
        # Vérifier les logs d'événements Windows
        try {
            $events = Get-EventLog -LogName Application -Source $serviceName -Newest 5 -ErrorAction SilentlyContinue
            if ($events) {
                Write-Host "  Derniers événements du service:" -ForegroundColor Yellow
                foreach ($event in $events) {
                    Write-Host "    [$($event.TimeGenerated)] $($event.EntryType): $($event.Message)" -ForegroundColor $(if($event.EntryType -eq 'Error'){'Red'}else{'Yellow'})
                }
            } else {
                # Chercher dans les événements système
                $systemEvents = Get-EventLog -LogName System -Newest 20 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match $serviceName }
                if ($systemEvents) {
                    Write-Host "  Événements système liés:" -ForegroundColor Yellow
                    foreach ($event in $systemEvents | Select-Object -First 3) {
                        Write-Host "    [$($event.TimeGenerated)] $($event.EntryType): $($event.Message.Substring(0, [Math]::Min(200, $event.Message.Length)))..." -ForegroundColor $(if($event.EntryType -eq 'Error'){'Red'}else{'Yellow'})
                    }
                }
            }
        } catch {
            Write-Host "  Impossible de lire les logs: $_" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Solutions possibles:" -ForegroundColor Yellow
        Write-Host "  1. Vérifiez que le fichier existe: $exporterPath" -ForegroundColor White
        Write-Host "  2. Testez manuellement: & `"$exporterPath`" $arguments" -ForegroundColor White
        Write-Host "  3. Vérifiez les permissions du service" -ForegroundColor White
        Write-Host "  4. Consultez l'Observateur d'événements Windows" -ForegroundColor White
        Write-Host ""
        Write-Host "Pour démarrer manuellement:" -ForegroundColor Cyan
        Write-Host "  Start-Service -Name '$serviceName'" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "[ERREUR] Erreur lors de la création/démarrage du service: $_" -ForegroundColor Red
    exit 1
}

# Vérifier que le port est accessible
Write-Host ""
Write-Host "[INFO] Vérification de l'exposition des métriques..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$serverHost = "sar-intranet.sar.sn"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$port/metrics" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Windows Exporter expose les métriques" -ForegroundColor Green
        Write-Host "  Local: http://localhost:$port/metrics" -ForegroundColor Cyan
        Write-Host "  Serveur: http://${serverHost}:${port}/metrics" -ForegroundColor Cyan
        $metricCount = ($response.Content -split "`n" | Where-Object { $_ -match "^[^#]" }).Count
        Write-Host "  Nombre de métriques exposées: $metricCount" -ForegroundColor Gray
    }
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de vérifier les métriques: $_" -ForegroundColor Yellow
    Write-Host "  Le service peut avoir besoin de plus de temps pour démarrer" -ForegroundColor Yellow
}

# Ouvrir le port dans le pare-feu (optionnel)
Write-Host ""
Write-Host "[INFO] Configuration du pare-feu..." -ForegroundColor Yellow
try {
    $firewallRule = Get-NetFirewallRule -DisplayName "Windows Exporter" -ErrorAction SilentlyContinue
    if (-not $firewallRule) {
        New-NetFirewallRule -DisplayName "Windows Exporter" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[OK] Règle de pare-feu créée pour le port $port" -ForegroundColor Green
    } else {
        Write-Host "[OK] Règle de pare-feu existe déjà" -ForegroundColor Green
    }
} catch {
    Write-Host "[AVERTISSEMENT] Impossible de configurer le pare-feu: $_" -ForegroundColor Yellow
    Write-Host "  Vous devrez peut-être ouvrir le port $port manuellement" -ForegroundColor Yellow
}

# Résumé
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installation terminée avec succès!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Résumé de l'installation:" -ForegroundColor Yellow
Write-Host "  ✓ Windows Exporter installé dans: $installDir" -ForegroundColor Green
Write-Host "  ✓ Service Windows: $serviceName" -ForegroundColor Green
Write-Host "  ✓ Port: $port" -ForegroundColor Green
Write-Host "  ✓ Collectors activés: $collectors" -ForegroundColor Green
Write-Host "  ✓ Démarrage automatique: Activé" -ForegroundColor Green
Write-Host ""
$serverHost = "sar-intranet.sar.sn"
Write-Host "URLs importantes:" -ForegroundColor Yellow
Write-Host "  Local: http://localhost:$port/metrics" -ForegroundColor Cyan
Write-Host "  Serveur: http://${serverHost}:${port}/metrics" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  # Vérifier le statut du service:" -ForegroundColor White
Write-Host "  Get-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Redémarrer le service:" -ForegroundColor White
Write-Host "  Restart-Service -Name '$serviceName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Voir les métriques:" -ForegroundColor White
Write-Host "  Invoke-WebRequest -Uri 'http://sar-intranet.sar.sn:${port}/metrics' | Select-Object -ExpandProperty Content" -ForegroundColor Cyan
Write-Host ""

