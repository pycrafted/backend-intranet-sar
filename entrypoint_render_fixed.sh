#!/bin/bash

echo "🚀 Démarrage du backend Django SAR sur Render..."
echo "📋 Configuration:"
echo "   - Settings: master.settings_production"
echo "   - Debug: False"
echo "   - Port: 10000"

# Vérifier les dépendances
echo "🔍 Vérification des dépendances..."
python -c "import django; print(f'Django {django.get_version()}')"
python -c "import psycopg2; print('PostgreSQL support OK')"
python -c "import gunicorn; print('Gunicorn OK')"

# Créer les répertoires nécessaires
echo "📁 Création des répertoires nécessaires..."
mkdir -p staticfiles
mkdir -p media
mkdir -p cache/models
mkdir -p backups
mkdir -p logs

# Appliquer les migrations
echo "🔄 Application des migrations Django..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer un superutilisateur si nécessaire (optionnel)
echo "👤 Configuration des utilisateurs..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur admin créé')
else:
    print('Superutilisateur admin existe déjà')
"

# Vérifier la santé du système
echo "🏥 Vérification de la santé du système..."
python manage.py check --deploy

# Démarrer l'application
echo "🚀 Démarrage de l'application Django..."
exec gunicorn master.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile -
