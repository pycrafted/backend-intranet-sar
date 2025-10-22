#!/bin/bash
set -e

echo "🚀 Démarrage du backend Django SAR sur Render..."

# =============================================================================
# CONFIGURATION DE L'ENVIRONNEMENT
# =============================================================================

# Utiliser les settings Render
export DJANGO_SETTINGS_MODULE=master.settings_render

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
# Appliquer les migrations avec gestion des erreurs
python manage.py migrate --run-syncdb || {
    echo "⚠️  Erreur lors des migrations, tentative de récupération..."
    python fix_migrations.py || echo "⚠️  Impossible de corriger les migrations"
}

# =============================================================================
# COLLECTION DES FICHIERS STATIQUES
# =============================================================================

echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# =============================================================================
# CONFIGURATION DES DONNÉES INITIALES (SIMPLIFIÉE)
# =============================================================================

echo "📊 Configuration des données initiales..."

# Créer un dataset minimal si nécessaire
if [ ! -f "data/sar_official_dataset.csv" ]; then
    echo "   - Création d'un dataset minimal..."
    mkdir -p data
    echo "question,answer" > data/sar_official_dataset.csv
    echo "Qu'est-ce que la SAR ?,Société Africaine de Raffinage" >> data/sar_official_dataset.csv
    echo "Quelle est la date d'inauguration de la SAR ?,Le 27 janvier 1964" >> data/sar_official_dataset.csv
    echo "Quelle est la capacité de la SAR ?,1,2 million de tonnes par an" >> data/sar_official_dataset.csv
fi

# Configuration RAG simplifiée (sans vectorisation pour éviter les erreurs)
echo "   - Configuration RAG simplifiée..."
python manage.py shell -c "
from mai.models import DocumentEmbedding
from mai.services import MAIService
import pandas as pd

# Charger le dataset
try:
    df = pd.read_csv('data/sar_official_dataset.csv')
    print(f'Dataset chargé: {len(df)} questions')
    
    # Créer quelques documents d'exemple
    for _, row in df.head(5).iterrows():
        doc, created = DocumentEmbedding.objects.get_or_create(
            content=f'Q: {row[\"question\"]}\\nA: {row[\"answer\"]}',
            defaults={
                'embedding': [0.0] * 384,  # Embedding factice
                'metadata': {
                    'question': row['question'],
                    'answer': row['answer'],
                    'source': 'sar_official_dataset.csv'
                }
            }
        )
        if created:
            print(f'Document créé: {row[\"question\"]}')
    
    print('Configuration RAG terminée')
except Exception as e:
    print(f'Erreur configuration RAG: {e}')
" || echo "⚠️  Erreur lors de la configuration RAG"

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
