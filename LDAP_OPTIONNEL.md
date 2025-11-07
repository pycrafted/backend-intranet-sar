# 🔧 LDAP Optionnel - Guide de Configuration

## ✅ Modifications Apportées

Le backend LDAP est maintenant **optionnel**. Si le serveur LDAP n'est pas accessible (ex: développement à domicile), le système utilisera automatiquement l'authentification locale (ModelBackend).

### Changements Principaux

1. **Variable d'environnement `LDAP_ENABLED`** : Active/désactive LDAP
2. **Gestion gracieuse des erreurs** : Les erreurs de connexion LDAP (timeout, serveur inaccessible) sont gérées silencieusement
3. **Timeouts configurés** : Timeout de 5 secondes pour éviter les blocages
4. **Fallback automatique** : Si LDAP échoue, Django passe au ModelBackend

## 📝 Configuration

### Pour Désactiver LDAP (Développement à Domicile)

Ajoutez dans votre fichier `.env` :

```env
LDAP_ENABLED=False
```

### Pour Activer LDAP (Bureau/Production)

```env
LDAP_ENABLED=True
LDAP_SERVER=10.113.243.2
LDAP_PORT=389
LDAP_BASE_DN=DC=sar,DC=sn
LDAP_BIND_DN=utilisateur@sar.sn
LDAP_BIND_PASSWORD=votre_mot_de_passe
```

## 🔍 Comportement

### Si LDAP est Activé mais Inaccessible

- Le backend LDAP essaie de se connecter avec un timeout de 5 secondes
- Si la connexion échoue, il retourne `None` silencieusement
- Django passe automatiquement au `ModelBackend` pour l'authentification locale
- Aucune erreur n'est levée, l'authentification continue normalement

### Si LDAP est Désactivé

- Le backend LDAP retourne immédiatement `None`
- Django utilise directement le `ModelBackend`

## ⚠️ Résolution de l'Erreur `phone_fixed`

Si vous voyez l'erreur :
```
ERREUR: la colonne authentication_user.phone_fixed n'existe pas
```

**Solution** : Appliquez la migration manquante :

```bash
python manage.py migrate authentication 0003_user_phone_fixed_user_phone_number
```

Si la migration a déjà été "faked" mais que la colonne n'existe pas, créez-la manuellement :

```sql
ALTER TABLE authentication_user ADD COLUMN phone_fixed VARCHAR(50) NULL;
ALTER TABLE authentication_user ADD COLUMN phone_number VARCHAR(50) NULL;
```

Puis marquez la migration comme appliquée :

```bash
python manage.py migrate --fake authentication 0003_user_phone_fixed_user_phone_number
```

## 🧪 Test

1. **Avec LDAP désactivé** :
   ```bash
   # Dans .env
   LDAP_ENABLED=False
   ```
   L'authentification doit fonctionner avec les comptes locaux Django.

2. **Avec LDAP activé mais serveur inaccessible** :
   ```bash
   # Dans .env
   LDAP_ENABLED=True
   LDAP_SERVER=10.113.243.2  # Serveur inaccessible depuis chez vous
   ```
   L'authentification doit fonctionner avec les comptes locaux Django (fallback automatique).

3. **Avec LDAP activé et accessible** :
   L'authentification LDAP fonctionne normalement.

## 📋 Logs

Les logs utilisent maintenant `logger.debug()` au lieu de `logger.error()` pour les erreurs LDAP non critiques, permettant un fonctionnement silencieux en cas d'indisponibilité du serveur.

