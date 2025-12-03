# Instructions pour supprimer les tables du forum

Ce dossier contient les scripts nécessaires pour supprimer définitivement les tables du module forum de la base de données PostgreSQL.

## ⚠️ ATTENTION

**Cette opération est irréversible !** Assurez-vous d'avoir fait une sauvegarde complète de votre base de données avant d'exécuter ces scripts.

## Fichiers inclus

1. **`remove_forum_tables.sql`** : Script SQL qui supprime les tables et nettoie les références Django
2. **`remove_forum_tables.ps1`** : Script PowerShell pour exécuter automatiquement le script SQL
3. **`remove_forum_tables_instructions.md`** : Ce fichier d'instructions

## Méthode 1 : Utilisation du script PowerShell (Recommandé)

### Prérequis
- PowerShell installé
- `psql` (client PostgreSQL) accessible dans votre PATH
- Variables d'environnement PostgreSQL configurées dans `.env`

### Étapes

1. Ouvrez PowerShell dans le dossier `backend-intranet-sar`
2. Exécutez le script :
   ```powershell
   .\remove_forum_tables.ps1
   ```
3. Confirmez en tapant `OUI` lorsque demandé
4. Le script exécutera automatiquement le fichier SQL

## Méthode 2 : Exécution manuelle du script SQL

### Prérequis
- Accès à la base de données PostgreSQL
- Client PostgreSQL (`psql`) installé

### Étapes

1. Connectez-vous à votre base de données PostgreSQL :
   ```bash
   psql -h <HOST> -p <PORT> -U <USER> -d <DATABASE>
   ```

2. Exécutez le script SQL :
   ```sql
   \i remove_forum_tables.sql
   ```
   
   Ou depuis la ligne de commande :
   ```bash
   psql -h <HOST> -p <PORT> -U <USER> -d <DATABASE> -f remove_forum_tables.sql
   ```

## Méthode 3 : Via pgAdmin ou un autre client SQL

1. Ouvrez votre client SQL (pgAdmin, DBeaver, etc.)
2. Connectez-vous à votre base de données
3. Ouvrez le fichier `remove_forum_tables.sql`
4. Exécutez le script complet

## Tables supprimées

Le script supprime les tables suivantes (dans l'ordre des dépendances) :

1. `forum_commentlike` - Table des likes sur les commentaires
2. `forum_comment` - Table des commentaires/posts
3. `forum_conversation` - Table des conversations (si elle existait)
4. `forum_forum` - Table principale des forums

## Nettoyage Django

Le script nettoie également :

- **django_content_type** : Supprime les enregistrements liés au forum
- **django_migrations** : Supprime les migrations liées au forum
- **auth_permission** : Supprime les permissions liées au forum (automatique via content types)

## Vérification après exécution

Après l'exécution, vous pouvez vérifier que tout a été supprimé :

```sql
-- Vérifier les tables restantes
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'forum_%';

-- Vérifier les content types restants
SELECT * FROM django_content_type WHERE app_label = 'forum';

-- Vérifier les migrations restantes
SELECT * FROM django_migrations WHERE app = 'forum';
```

Toutes ces requêtes devraient retourner des résultats vides.

## En cas de problème

Si vous rencontrez des erreurs :

1. **Erreur de permissions** : Assurez-vous que l'utilisateur PostgreSQL a les droits nécessaires
2. **Tables déjà supprimées** : Le script utilise `DROP TABLE IF EXISTS`, donc il ne générera pas d'erreur si les tables n'existent pas
3. **Erreur de connexion** : Vérifiez vos paramètres de connexion dans `.env`

## Support

Si vous avez des questions ou rencontrez des problèmes, consultez la documentation Django sur les migrations ou contactez votre administrateur de base de données.


