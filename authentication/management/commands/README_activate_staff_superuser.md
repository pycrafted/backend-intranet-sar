# Script d'activation du statut Staff et Superuser

Ce script permet d'activer le statut **Staff** et **Superuser** pour tous les utilisateurs Django.

## 📋 Description

Le statut **Staff** permet aux utilisateurs de se connecter à l'interface d'administration Django (`/admin/`).

Le statut **Superuser** donne tous les droits d'administration (création, modification, suppression de tous les objets).

## 🚀 Utilisation

### Activer Staff et Superuser pour tous les utilisateurs

```bash
python manage.py activate_staff_superuser_all
```

### Activer uniquement le statut Staff

```bash
python manage.py activate_staff_superuser_all --staff-only
```

### Activer uniquement le statut Superuser

```bash
python manage.py activate_staff_superuser_all --superuser-only
```

### Mode dry-run (simulation sans modification)

Pour voir ce qui serait fait sans modifier la base de données :

```bash
python manage.py activate_staff_superuser_all --dry-run
```

## ⚠️ Avertissements

- **Cette opération donne des privilèges élevés à tous les utilisateurs**
- Assurez-vous que c'est bien ce que vous voulez avant d'exécuter le script
- Utilisez `--dry-run` pour vérifier les modifications avant de les appliquer

## 📊 Exemple de sortie

```
================================================================================
🔐 ACTIVATION DU STATUT STAFF ET SUPERUSER POUR TOUS LES UTILISATEURS
================================================================================

📋👑 Mode: Activation des statuts STAFF et SUPERUSER

📊 150 utilisateur(s) trouvé(s) au total
✅ 25 utilisateur(s) déjà configuré(s)
🔄 125 utilisateur(s) à mettre à jour

✅ 125 utilisateur(s) mis à jour avec succès

📋 Exemples d'utilisateurs mis à jour:
  - user1@example.com                    | John Doe | Statuts: Staff, Superuser
  - user2@example.com                    | Jane Smith | Statuts: Staff, Superuser
  ...

================================================================================
✅ Opération terminée !
💡 Tous les utilisateurs ont maintenant le statut STAFF (accès à l'admin)
💡 Tous les utilisateurs ont maintenant le statut SUPERUSER (tous les droits)
================================================================================
```

## 🔧 Options disponibles

- `--dry-run` : Mode simulation, n'effectue aucune modification
- `--staff-only` : Active uniquement le statut Staff
- `--superuser-only` : Active uniquement le statut Superuser

## 📝 Notes

- Le script met à jour uniquement les utilisateurs qui n'ont pas déjà les statuts activés
- Les utilisateurs déjà configurés ne sont pas modifiés
- Le script affiche un résumé des modifications effectuées

