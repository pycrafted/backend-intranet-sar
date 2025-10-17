#!/bin/bash

# Script d'entrée pour Render avec population de données
echo "🚀 Démarrage de l'application avec données de test..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
python manage.py migrate --noinput

# Peupler l'organigramme avec des données de test
echo "📊 Population de l'organigramme avec des données de test..."
python manage.py populate_organigramme

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrer l'application
echo "🎉 Démarrage de l'application..."
exec gunicorn master.wsgi:application --bind 0.0.0.0:$PORT --workers 2
