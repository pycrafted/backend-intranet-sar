# Module Métriques

Module Django pour le suivi des métriques et statistiques de l'intranet SAR.

## Fonctionnalités

- **Tracking automatique des connexions** : Enregistre chaque connexion utilisateur avec l'IP, le User Agent et l'heure
- **Statistiques de connexions** : Connexions journalières, hebdomadaires et mensuelles
- **Métriques de l'application** : Nombre d'utilisateurs, articles, documents, messages forum
- **Dashboard administrateur** : Interface graphique pour visualiser toutes les métriques

## Installation

1. Le module est déjà ajouté dans `INSTALLED_APPS` dans `master/settings.py`
2. Les URLs sont configurées dans `master/urls.py`
3. Créer les migrations :
   ```bash
   python manage.py makemigrations metriques
   python manage.py migrate
   ```

## Modèles

### UserLogin
Enregistre chaque connexion utilisateur :
- `user` : Utilisateur connecté
- `login_time` : Heure de connexion
- `logout_time` : Heure de déconnexion (optionnel)
- `ip_address` : Adresse IP
- `user_agent` : User Agent du navigateur
- `session_duration` : Durée de la session (calculée automatiquement)

### AppMetric
Stocke des métriques générales de l'application (pour usage futur).

## API Endpoints

### GET /api/metriques/summary/
Récupère un résumé complet des métriques (admin uniquement).

**Réponse :**
```json
{
  "daily_logins": 45,
  "weekly_logins": 320,
  "monthly_logins": 1200,
  "total_users": 150,
  "active_users_today": 35,
  "active_users_week": 120,
  "active_users_month": 140,
  "total_articles": 500,
  "total_documents": 200,
  "total_forum_posts": 1500,
  "login_trend_daily": [...],
  "login_trend_weekly": [...],
  "login_trend_monthly": [...],
  "top_users": [...]
}
```

### GET /api/metriques/logins/
Liste des connexions avec filtrage (admin voit tout, utilisateur voit ses propres connexions).

**Paramètres de requête :**
- `user_id` : Filtrer par utilisateur (admin uniquement)
- `date_from` : Date de début (format YYYY-MM-DD)
- `date_to` : Date de fin (format YYYY-MM-DD)

### GET /api/metriques/login-stats/
Statistiques détaillées des connexions.

**Paramètres de requête :**
- `period` : `daily`, `weekly`, ou `monthly`

## Signaux

Le module utilise des signaux Django pour tracker automatiquement :
- `user_logged_in` : Crée un enregistrement UserLogin à chaque connexion
- `user_logged_out` : Met à jour l'enregistrement avec l'heure de déconnexion et calcule la durée

## Frontend

Le dashboard est accessible à `/metriques` et est réservé aux administrateurs.

Il affiche :
- Cartes de métriques principales (connexions du jour/semaine/mois, total utilisateurs)
- Graphiques de tendances (quotidien, hebdomadaire, mensuel)
- Top 10 des utilisateurs les plus actifs
- Métriques de contenu (articles, documents, messages forum)
