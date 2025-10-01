# Plan de Déploiement Backend SAR sur Render

## 📋 Analyse du Backend Actuel

### Structure du Projet
- **Framework**: Django 5.2.6 avec Django REST Framework
- **Base de données**: PostgreSQL avec pgvector pour RAG
- **Authentification**: Django Allauth avec OAuth Google
- **Fonctionnalités**: RAG (Retrieval Augmented Generation), gestion de documents, annuaire, actualités
- **Dépendances**: 93 packages incluant ML/AI (torch, sentence-transformers, faiss-cpu)

### Applications Django
1. **authentication** - Gestion des utilisateurs et OAuth
2. **actualites** - Système d'actualités
3. **annuaire** - Annuaire des employés
4. **accueil** - Dashboard et données de sécurité
5. **mai** - Chatbot RAG basé sur CSV
6. **documents** - Gestion des documents et dossiers
7. **health** - Endpoints de santé

### Dépendances Critiques
- **ML/AI**: torch, sentence-transformers, faiss-cpu, langchain
- **Base de données**: psycopg2-binary, pgvector
- **Authentification**: django-allauth, google-auth
- **API**: djangorestframework, django-cors-headers
- **Production**: gunicorn, whitenoise

## 🚨 Problèmes Identifiés

### 1. Commandes de Gestion Manquantes
- `import_sar_dataset` - Référencée dans entrypoint.sh mais non trouvée
- `setup_rag` - Référencée dans entrypoint.sh mais non trouvée

### 2. Configuration de Production
- DEBUG=True en production
- SECRET_KEY exposée
- CORS configuré pour localhost uniquement
- Pas de configuration pour fichiers statiques en production

### 3. Dépendances Lourdes
- torch (2.8.0) - Très lourd pour Render
- sentence-transformers avec modèles ML
- faiss-cpu pour recherche vectorielle

## 📝 Plan de Déploiement

### Phase 1: Préparation des Commandes Manquantes

#### 1.1 Créer la commande `import_sar_dataset`
```python
# backend/mai/management/commands/import_sar_dataset.py
from django.core.management.base import BaseCommand
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Importe le dataset SAR depuis un fichier CSV'
    
    def add_arguments(self, parser):
        parser.add_argument('--csv-file', type=str, required=True)
    
    def handle(self, *args, **options):
        # Implémentation de l'import du dataset
        pass
```

#### 1.2 Créer la commande `setup_rag`
```python
# backend/mai/management/commands/setup_rag.py
from django.core.management.base import BaseCommand
from mai.services import MAIService

class Command(BaseCommand):
    help = 'Configure le système RAG'
    
    def add_arguments(self, parser):
        parser.add_argument('--vectorize', action='store_true')
    
    def handle(self, *args, **options):
        # Configuration du système RAG
        pass
```

### Phase 2: Configuration de Production

#### 2.1 Créer `settings_production.py`
```python
# backend/master/settings_production.py
from .settings import *
import os

# Sécurité
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

# Base de données Render PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}

# CORS pour production
CORS_ALLOWED_ORIGINS = [
    os.environ.get('FRONTEND_URL', 'https://sar-connect.onrender.com'),
]

# Fichiers statiques
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 2.2 Créer `requirements_render.txt`
```txt
# Dépendances essentielles pour Render
Django==5.2.6
djangorestframework==3.16.1
django-cors-headers==4.7.0
django-filter==25.1
django-allauth==65.11.2
psycopg2-binary==2.9.10
gunicorn==21.2.0
whitenoise==6.6.0
python-decouple==3.8
pillow==11.3.0

# RAG optimisé pour production
sentence-transformers==2.7.0
faiss-cpu==1.7.4
langchain==0.1.0
pgvector==0.2.4
numpy==1.24.3

# OAuth Google
google-auth==2.41.0
google-auth-oauthlib==1.2.2
```

### Phase 3: Configuration Render

#### 3.1 Variables d'Environnement Render
```
SECRET_KEY=<générer une nouvelle clé sécurisée>
DEBUG=False
POSTGRES_DB=<nom de la DB Render>
POSTGRES_USER=<utilisateur DB Render>
POSTGRES_PASSWORD=<mot de passe DB Render>
POSTGRES_HOST=<host DB Render>
POSTGRES_PORT=5432
FRONTEND_URL=https://votre-frontend.onrender.com
GOOGLE_OAUTH2_CLIENT_ID=<votre client ID>
GOOGLE_OAUTH2_CLIENT_SECRET=<votre client secret>
CLAUDE_API_KEY=<votre clé Claude>
```

#### 3.2 Build Command Render
```bash
pip install -r requirements_render.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_default_categories
python manage.py import_sar_dataset --csv-file data/sar_official_dataset.csv
python manage.py setup_rag --vectorize
```

#### 3.3 Start Command Render
```bash
gunicorn master.wsgi:application --bind 0.0.0.0:$PORT
```

### Phase 4: Optimisations pour Render

#### 4.1 Réduire la taille des dépendances
- Utiliser `requirements_render.txt` avec versions optimisées
- Exclure torch si possible (utiliser CPU-only)
- Optimiser sentence-transformers

#### 4.2 Configuration des fichiers statiques
- Utiliser WhiteNoise pour servir les fichiers statiques
- Configurer `STATICFILES_STORAGE`
- Optimiser la collecte des fichiers statiques

#### 4.3 Gestion des médias
- Utiliser un service de stockage externe (AWS S3, Cloudinary)
- Ou configurer le stockage local avec persistance

### Phase 5: Tests et Validation

#### 5.1 Tests locaux
- Tester avec `settings_production.py`
- Vérifier les migrations
- Tester les endpoints API
- Valider le système RAG

#### 5.2 Tests sur Render
- Déploiement initial
- Test des fonctionnalités critiques
- Vérification des performances
- Test de la base de données

## 🔧 Actions Immédiates

### 1. Créer les commandes manquantes
- [x] `import_sar_dataset.py` ✅
- [x] `setup_rag.py` ✅

### 2. Créer la configuration de production
- [x] `settings_production.py` ✅
- [x] `requirements_render.txt` ✅

### 3. Optimiser les dépendances
- [x] Créer une version allégée des requirements ✅
- [ ] Tester la compatibilité avec Render

### 4. Préparer les fichiers de déploiement
- [x] `render.yaml` ✅
- [x] `entrypoint_render.sh` ✅
- [x] `test_render_config.py` ✅
- [x] `GUIDE_DEPLOIEMENT_RENDER.md` ✅

### 5. Actions Restantes
- [ ] Tester la configuration localement
- [ ] Valider les commandes de gestion
- [ ] Tester le déploiement sur Render
- [ ] Optimiser les performances

## ⚠️ Considérations Importantes

### Limitations Render
- **Mémoire**: Limite de 512MB sur le plan gratuit
- **CPU**: Limité, peut impacter les opérations ML
- **Stockage**: Éphémère, nécessite stockage externe pour médias
- **Timeout**: 30 secondes max par requête

### Recommandations
1. **Commencer par un déploiement minimal** sans RAG
2. **Tester les performances** avec les dépendances ML
3. **Considérer un upgrade** vers un plan payant si nécessaire
4. **Utiliser un CDN** pour les fichiers statiques
5. **Implémenter la mise en cache** pour les requêtes lourdes

## 📊 Métriques de Succès

- [ ] Déploiement réussi sans erreurs
- [ ] Toutes les migrations appliquées
- [ ] API fonctionnelle
- [ ] Authentification OAuth opérationnelle
- [ ] Système RAG fonctionnel (si possible)
- [ ] Temps de réponse < 5 secondes
- [ ] Utilisation mémoire < 400MB

## 🚀 Prochaines Étapes

1. **Créer les commandes manquantes**
2. **Configurer la production**
3. **Tester localement**
4. **Déployer sur Render**
5. **Valider et optimiser**

---

*Ce plan sera mis à jour au fur et à mesure de l'implémentation.*
