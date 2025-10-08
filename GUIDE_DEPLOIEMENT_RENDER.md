# Guide de Déploiement Backend SAR sur Render

## 🎯 Vue d'ensemble

Ce guide vous accompagne étape par étape pour déployer le backend Django SAR sur Render, une plateforme de déploiement cloud moderne et simple.

## 📋 Prérequis

### 1. Compte Render
- Créer un compte sur [render.com](https://render.com)
- Vérifier l'email (obligatoire)

### 2. Repository Git
- Code backend dans un repository Git (GitHub, GitLab, Bitbucket)
- Repository accessible publiquement ou connecté à Render

### 3. Variables d'environnement
- Clé API Claude (pour le système RAG)
- Credentials OAuth Google (optionnel)
- URL du frontend (si déployé séparément)

## 🚀 Déploiement Automatique (Recommandé)

### Étape 1: Configuration du Repository
```bash
# Dans le répertoire backend
git add .
git commit -m "Préparation déploiement Render"
git push origin main
```

### Étape 2: Création du Service sur Render

1. **Aller sur [render.com](https://render.com)**
2. **Cliquer sur "New +" → "Web Service"**
3. **Connecter le repository**
4. **Configurer le service:**
   - **Name**: `sar-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements_render.txt`
   - **Start Command**: `chmod +x entrypoint_render.sh && ./entrypoint_render.sh`

### Étape 3: Configuration des Variables d'Environnement

Dans l'onglet "Environment" du service Render :

```bash
# Configuration Django
DJANGO_SETTINGS_MODULE=master.settings_production
DEBUG=False
SECRET_KEY=<généré automatiquement par Render>

# Configuration CORS (remplacer par votre URL frontend)
FRONTEND_URL=https://votre-frontend.onrender.com

# Configuration Claude API (obligatoire pour RAG)
CLAUDE_API_KEY=sk-ant-api03-votre-clé-claude

# Configuration OAuth Google (optionnel)
GOOGLE_OAUTH2_CLIENT_ID=votre-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=votre-client-secret

# Configuration des workers
WORKERS=2
```

### Étape 4: Création de la Base de Données

1. **Aller sur "New +" → "PostgreSQL"**
2. **Configurer la base de données:**
   - **Name**: `sar-db`
   - **Database**: `sar`
   - **User**: `sar_user`
   - **Plan**: `Free` (pour commencer)

3. **Copier les variables de connexion:**
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`

4. **Ajouter ces variables au service web**

### Étape 5: Déploiement

1. **Cliquer sur "Create Web Service"**
2. **Attendre la fin du build** (5-10 minutes)
3. **Vérifier les logs** pour s'assurer du succès

## 🔧 Déploiement Manuel (Avancé)

### Étape 1: Test Local
```bash
# Tester la configuration
python test_render_config.py

# Tester avec les settings de production
export DJANGO_SETTINGS_MODULE=master.settings_production
python manage.py check --deploy
```

### Étape 2: Configuration Render.yaml
Si vous utilisez le fichier `render.yaml` :

1. **Placer le fichier à la racine du repository**
2. **Modifier les variables d'environnement dans le fichier**
3. **Utiliser "New +" → "Blueprint" sur Render**
4. **Sélectionner le repository avec render.yaml**

## 🧪 Tests Post-Déploiement

### 1. Test de Santé
```bash
curl https://votre-backend.onrender.com/api/health/
```

**Réponse attendue:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### 2. Test des Endpoints API
```bash
# Test de l'API d'authentification
curl https://votre-backend.onrender.com/api/auth/check/

# Test de l'API des actualités
curl https://votre-backend.onrender.com/api/actualites/

# Test de l'API des documents
curl https://votre-backend.onrender.com/api/documents/
```

### 3. Test du Système RAG
```bash
# Test du chatbot MAI
curl -X POST https://votre-backend.onrender.com/api/mai/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Qu\'est-ce que la SAR ?"}'
```

## 🔍 Résolution des Problèmes

### Problème 1: Build Failed
**Symptômes:** Le build échoue avec des erreurs de dépendances

**Solutions:**
```bash
# Vérifier les requirements
pip install -r requirements_render.txt

# Tester localement
python test_render_config.py
```

### Problème 2: Database Connection Error
**Symptômes:** Erreurs de connexion à la base de données

**Solutions:**
1. Vérifier les variables d'environnement PostgreSQL
2. S'assurer que la base de données est créée
3. Vérifier les credentials

### Problème 3: Static Files Not Found
**Symptômes:** Erreurs 404 pour les fichiers statiques

**Solutions:**
1. Vérifier que `collectstatic` s'exécute
2. Vérifier la configuration WhiteNoise
3. Vérifier `STATIC_ROOT`

### Problème 4: RAG Not Working
**Symptômes:** Le chatbot ne répond pas

**Solutions:**
1. Vérifier `CLAUDE_API_KEY`
2. Vérifier l'import du dataset
3. Vérifier les logs pour les erreurs ML

### Problème 5: CORS Errors
**Symptômes:** Erreurs CORS dans le frontend

**Solutions:**
1. Vérifier `FRONTEND_URL`
2. Vérifier `CORS_ALLOWED_ORIGINS`
3. Vérifier la configuration du frontend

## 📊 Monitoring et Maintenance

### 1. Logs
- **Dashboard Render** → Service → Logs
- **Logs en temps réel** disponibles
- **Logs historiques** pour le debugging

### 2. Métriques
- **CPU Usage** - Surveiller l'utilisation
- **Memory Usage** - Important pour les opérations ML
- **Response Time** - Performance des API
- **Error Rate** - Taux d'erreurs

### 3. Maintenance
```bash
# Redémarrage du service
# Dashboard Render → Service → Manual Deploy

# Mise à jour des dépendances
# Modifier requirements_render.txt et redéployer

# Sauvegarde de la base de données
# Dashboard Render → Database → Backups
```

## 🚀 Optimisations

### 1. Performance
- **Upgrade vers un plan payant** pour plus de ressources
- **Utiliser un CDN** pour les fichiers statiques
- **Implémenter la mise en cache** Redis
- **Optimiser les requêtes** de base de données

### 2. Sécurité
- **Utiliser HTTPS** (automatique sur Render)
- **Configurer les headers de sécurité**
- **Limiter les taux de requêtes**
- **Auditer les logs** régulièrement

### 3. Scalabilité
- **Auto-scaling** avec les plans payants
- **Load balancing** pour haute disponibilité
- **Database clustering** pour les gros volumes
- **Microservices** pour la séparation des responsabilités

## 📈 Évolutions Futures

### 1. Plan Payant
- **Plus de RAM** pour les opérations ML
- **Pas de sleep** automatique
- **Meilleures performances**
- **Support prioritaire**

### 2. Services Additionnels
- **Redis** pour la mise en cache
- **Elasticsearch** pour la recherche
- **S3** pour le stockage des médias
- **CloudFront** pour le CDN

### 3. Monitoring Avancé
- **New Relic** ou **DataDog** pour l'APM
- **Sentry** pour le tracking d'erreurs
- **Grafana** pour les métriques
- **PagerDuty** pour les alertes

## 🆘 Support

### 1. Documentation
- [Render Documentation](https://render.com/docs)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

### 2. Communauté
- [Render Community](https://community.render.com/)
- [Django Forum](https://forum.djangoproject.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/django+render)

### 3. Support Render
- **Plan gratuit**: Support communautaire
- **Plan payant**: Support email prioritaire
- **Enterprise**: Support téléphonique

---

## ✅ Checklist de Déploiement

- [ ] Repository Git configuré
- [ ] Variables d'environnement définies
- [ ] Base de données PostgreSQL créée
- [ ] Service web configuré
- [ ] Build réussi
- [ ] Tests de santé passés
- [ ] API endpoints fonctionnels
- [ ] Système RAG opérationnel
- [ ] Frontend connecté
- [ ] Monitoring configuré

**🎉 Félicitations! Votre backend SAR est déployé sur Render!**




