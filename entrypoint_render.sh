#!/bin/bash
set -e

echo "🚀 Démarrage du backend Django SAR sur Render..."

# =============================================================================
# CONFIGURATION DE L'ENVIRONNEMENT
# =============================================================================

# Utiliser les settings de production
export DJANGO_SETTINGS_MODULE=master.settings_production

# Afficher les informations de configuration
echo "📋 Configuration:"
echo "   - Settings: $DJANGO_SETTINGS_MODULE"
echo "   - Debug: ${DEBUG:-False}"
echo "   - Port: ${PORT:-8000}"

# =============================================================================
# VÉRIFICATION DES DÉPENDANCES
# =============================================================================

echo "🔍 Vérification des dépendances..."
python -c "import django; print(f'Django {django.get_version()}')"
python -c "import psycopg2; print('PostgreSQL support OK')"
python -c "import gunicorn; print('Gunicorn OK')"

# =============================================================================
# MIGRATIONS DE BASE DE DONNÉES
# =============================================================================

echo "🔄 Application des migrations Django..."
python manage.py migrate --run-syncdb

# =============================================================================
# COLLECTION DES FICHIERS STATIQUES
# =============================================================================

echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# =============================================================================
# CONFIGURATION DES DONNÉES INITIALES
# =============================================================================

echo "📊 Configuration des données initiales..."

# Créer les catégories de documents par défaut
echo "   - Création des catégories de documents..."
python manage.py create_default_categories || echo "⚠️  Erreur lors de la création des catégories"

# Importer le dataset SAR si disponible
if [ -f "data/sar_official_dataset.csv" ]; then
    echo "   - Importation du dataset SAR..."
    python manage.py import_sar_dataset --csv-file data/sar_official_dataset.csv || echo "⚠️  Erreur lors de l'import du dataset"
else
    echo "   - Dataset SAR non trouvé, création d'un dataset minimal..."
    mkdir -p data
    echo "question,answer" > data/sar_official_dataset.csv
    echo "Qu'est-ce que la SAR ?,Société Africaine de Raffinage" >> data/sar_official_dataset.csv
    python manage.py import_sar_dataset --csv-file data/sar_official_dataset.csv || echo "⚠️  Erreur lors de l'import du dataset minimal"
fi

# Configurer le système RAG
echo "   - Configuration du système RAG..."
python manage.py setup_rag --vectorize || echo "⚠️  Erreur lors de la configuration RAG"

# =============================================================================
# CRÉATION DU SUPERUTILISATEUR
# =============================================================================

echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sar.sn', 'admin123')
    print('✅ Superutilisateur créé: admin/admin123')
else:
    print('✅ Superutilisateur existe déjà')
" || echo "⚠️  Erreur lors de la création du superutilisateur"

# =============================================================================
# VÉRIFICATION DE LA SANTÉ DE L'APPLICATION
# =============================================================================

echo "🏥 Vérification de la santé de l'application..."
python manage.py check --deploy || echo "⚠️  Avertissements de déploiement détectés"

# =============================================================================
# DÉMARRAGE DU SERVEUR
# =============================================================================

echo "✅ Backend Django prêt!"
echo "🌐 Démarrage du serveur sur le port ${PORT:-8000}"

# Démarrer Gunicorn avec la configuration optimisée pour Render
exec gunicorn master.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile -
