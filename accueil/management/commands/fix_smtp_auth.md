# Guide pour activer l'authentification SMTP dans Office 365

## Problème
L'erreur `SmtpClientAuthentication is disabled for the Tenant` indique que l'authentification basique SMTP est désactivée sur votre tenant Office 365.

## Solution 1 : Activer l'authentification SMTP basique (Recommandé pour les tests)

### Via PowerShell (Exchange Online)
```powershell
# Se connecter à Exchange Online
Connect-ExchangeOnline

# Activer l'authentification SMTP pour un utilisateur spécifique
Set-CASMailbox -Identity "AbdoulayeLAH.external@sar.sn" -SmtpClientAuthenticationDisabled $false

# Ou activer pour tous les utilisateurs (moins sécurisé)
Get-CASMailbox | Set-CASMailbox -SmtpClientAuthenticationDisabled $false
```

### Via Microsoft 365 Admin Center
1. Aller sur https://admin.microsoft.com
2. Paramètres > Paramètres > Paramètres de sécurité
3. Activer "Authentification SMTP AUTH" pour les utilisateurs concernés

## Solution 2 : Utiliser OAuth 2.0 (Recommandé pour la production)

Microsoft recommande OAuth 2.0 depuis octobre 2022. Cela nécessite :
- Enregistrer une application dans Azure AD
- Obtenir un client_id, client_secret, tenant_id
- Utiliser une librairie comme `O365` ou créer un backend custom

## Solution 3 : Utiliser un serveur SMTP Exchange on-premise (si disponible)

Si votre entreprise a un serveur Exchange on-premise, vous pouvez utiliser son serveur SMTP au lieu d'Office 365.


