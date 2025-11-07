# Guide d'Export/Import de la Base de Données PostgreSQL

## 📤 EXPORT (Sur la machine source - Windows)

### Méthode 1 : Export en format SQL (recommandé pour la compatibilité)

```bash
# Ouvrir PowerShell ou CMD dans le dossier du projet
cd C:\Users\hp\Desktop\intranet\backend-intranet-sar

# Export complet de la base de données
pg_dump -h localhost -p 5432 -U sar_user -d sar -F p -f backup_sar_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Vous serez demandé le mot de passe : sar123
```

**Alternative avec mot de passe dans la commande (moins sécurisé) :**
```bash
$env:PGPASSWORD="sar123"
pg_dump -h localhost -p 5432 -U sar_user -d sar -F p -f backup_sar_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

### Méthode 2 : Export en format custom (plus compact, recommandé pour grandes bases)

```bash
# Export en format custom (compressé)
pg_dump -h localhost -p 5432 -U sar_user -d sar -F c -f backup_sar_$(Get-Date -Format "yyyyMMdd_HHmmss").dump

# Vous serez demandé le mot de passe : sar123
```

### Méthode 3 : Export avec compression gzip (pour économiser l'espace)

```bash
# Export avec compression
pg_dump -h localhost -p 5432 -U sar_user -d sar -F p | gzip > backup_sar_$(Get-Date -Format "yyyyMMdd_HHmmss").sql.gz
```

### Options utiles pour pg_dump :

- `-F p` : Format SQL plain text (lisible, compatible)
- `-F c` : Format custom (compressé, plus rapide)
- `-F t` : Format tar
- `-f fichier` : Nom du fichier de sortie
- `--clean` : Ajoute des commandes DROP avant CREATE (utile pour réimport)
- `--if-exists` : Utilise IF EXISTS avec DROP (évite les erreurs)
- `--no-owner` : N'inclut pas les commandes de propriétaire
- `--no-privileges` : N'inclut pas les commandes de permissions

**Exemple avec options recommandées :**
```bash
pg_dump -h localhost -p 5432 -U sar_user -d sar -F p --clean --if-exists --no-owner --no-privileges -f backup_sar_complete.sql
```

---

## 📥 IMPORT (Sur la machine de destination - Windows)

### Prérequis sur la machine de destination :

1. **Installer PostgreSQL** (si pas déjà installé)
2. **Créer la base de données et l'utilisateur** :

```sql
-- Se connecter à PostgreSQL en tant que superuser (postgres)
psql -U postgres

-- Dans psql, exécuter :
CREATE DATABASE sar;
CREATE USER sar_user WITH PASSWORD 'sar123';
GRANT ALL PRIVILEGES ON DATABASE sar TO sar_user;
\q
```

### Méthode 1 : Import depuis fichier SQL

```bash
# Se placer dans le dossier contenant le fichier de backup
cd C:\chemin\vers\le\backup

# Import depuis fichier SQL
psql -h localhost -p 5432 -U sar_user -d sar -f backup_sar_YYYYMMDD_HHMMSS.sql

# Vous serez demandé le mot de passe : sar123
```

**Alternative avec mot de passe :**
```bash
$env:PGPASSWORD="sar123"
psql -h localhost -p 5432 -U sar_user -d sar -f backup_sar_YYYYMMDD_HHMMSS.sql
```

### Méthode 2 : Import depuis fichier custom (.dump)

```bash
# Import depuis fichier custom
pg_restore -h localhost -p 5432 -U sar_user -d sar -c backup_sar_YYYYMMDD_HHMMSS.dump

# Options utiles :
# -c : Clean (supprime les objets existants avant de créer)
# -v : Verbose (affiche les détails)
# -e : Exit on error (arrête en cas d'erreur)
```

### Méthode 3 : Import depuis fichier compressé (.sql.gz)

```bash
# Décompresser et importer en une commande
gunzip -c backup_sar_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -p 5432 -U sar_user -d sar
```

---

## 🔧 Commandes Complètes Recommandées

### Export (Machine Source)

```powershell
# Définir le mot de passe
$env:PGPASSWORD="sar123"

# Export avec toutes les options recommandées
pg_dump -h localhost -p 5432 -U sar_user -d sar `
    -F p `
    --clean `
    --if-exists `
    --no-owner `
    --no-privileges `
    --verbose `
    -f "backup_sar_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"

Write-Host "✅ Export terminé avec succès !"
```

### Import (Machine Destination)

```powershell
# Définir le mot de passe
$env:PGPASSWORD="sar123"

# Import avec gestion des erreurs
psql -h localhost -p 5432 -U sar_user -d sar `
    -f "backup_sar_YYYYMMDD_HHMMSS.sql" `
    -v ON_ERROR_STOP=1

Write-Host "✅ Import terminé avec succès !"
```

---

## 📋 Checklist de Migration

### Sur la machine source :
- [ ] Vérifier que PostgreSQL est en cours d'exécution
- [ ] Vérifier les credentials dans `.env`
- [ ] Exécuter la commande d'export
- [ ] Vérifier que le fichier de backup a été créé
- [ ] Copier le fichier de backup vers la machine de destination (USB, réseau, etc.)

### Sur la machine de destination :
- [ ] Installer PostgreSQL (même version ou supérieure)
- [ ] Créer la base de données `sar`
- [ ] Créer l'utilisateur `sar_user` avec le mot de passe
- [ ] Donner les permissions à l'utilisateur
- [ ] Copier le fichier de backup sur la machine
- [ ] Exécuter la commande d'import
- [ ] Vérifier que les données sont présentes

---

## ⚠️ Notes Importantes

1. **Version PostgreSQL** : Il est recommandé d'utiliser la même version (ou supérieure) de PostgreSQL sur les deux machines pour éviter les problèmes de compatibilité.

2. **Taille du fichier** : Pour de grandes bases de données, utilisez le format custom (`.dump`) qui est compressé.

3. **Permissions** : Si vous avez des problèmes de permissions, utilisez `--no-owner` et `--no-privileges` lors de l'export.

4. **Extensions PostgreSQL** : Si vous utilisez des extensions (comme pgvector), assurez-vous qu'elles sont installées sur la machine de destination avant l'import.

5. **Médias/Fichiers** : N'oubliez pas de copier aussi le dossier `media/` qui contient les fichiers uploadés (avatars, documents, etc.).

---

## 🚀 Script PowerShell Automatisé

Créez un fichier `export_database.ps1` :

```powershell
# Configuration
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_USER = "sar_user"
$DB_NAME = "sar"
$DB_PASSWORD = "sar123"
$BACKUP_DIR = "C:\Users\hp\Desktop\intranet\backups"

# Créer le dossier de backup s'il n'existe pas
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR
}

# Nom du fichier avec timestamp
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = Join-Path $BACKUP_DIR "backup_sar_$TIMESTAMP.sql"

# Définir le mot de passe
$env:PGPASSWORD = $DB_PASSWORD

Write-Host "🔄 Export de la base de données en cours..." -ForegroundColor Yellow

# Export
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
    -F p `
    --clean `
    --if-exists `
    --no-owner `
    --no-privileges `
    --verbose `
    -f $BACKUP_FILE

if ($LASTEXITCODE -eq 0) {
    $FILE_SIZE = (Get-Item $BACKUP_FILE).Length / 1MB
    Write-Host "✅ Export réussi !" -ForegroundColor Green
    Write-Host "📁 Fichier : $BACKUP_FILE" -ForegroundColor Cyan
    Write-Host "📊 Taille : $([math]::Round($FILE_SIZE, 2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erreur lors de l'export !" -ForegroundColor Red
    exit 1
}
```

---

## 🔍 Vérification après Import

```sql
-- Se connecter à la base de données
psql -U sar_user -d sar

-- Vérifier les tables
\dt

-- Compter les enregistrements dans quelques tables importantes
SELECT COUNT(*) FROM annuaire_employee;
SELECT COUNT(*) FROM authentication_user;
SELECT COUNT(*) FROM organigramme_agent;
SELECT COUNT(*) FROM forum_forum;

-- Quitter
\q
```

