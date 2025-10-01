#!/bin/bash
set -e

echo "🚀 Démarrage du backend Django SAR..."

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente de PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "   PostgreSQL n'est pas encore prêt, attente..."
  sleep 2
done
echo "✅ PostgreSQL est prêt!"

# Appliquer les migrations
echo "🔄 Application des migrations Django..."
python manage.py migrate --run-syncdb || echo "⚠️  Erreur lors des migrations, continuation..."

# Collecter les fichiers statiques
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Importer le dataset SAR si il n'existe pas
echo "📊 Vérification du dataset SAR..."
if [ ! -f "data/sar_official_dataset.csv" ]; then
    echo "⚠️  Dataset SAR non trouvé, création d'un dataset vide..."
    mkdir -p data
    echo "question,answer" > data/sar_official_dataset.csv
    echo "Qu'est-ce que la SAR ?,Société Africaine de Raffinage" >> data/sar_official_dataset.csv
fi

# Importer le dataset SAR
echo "📥 Importation du dataset SAR..."
python manage.py import_sar_dataset --csv-file data/sar_official_dataset.csv || echo "⚠️  Erreur lors de l'import du dataset SAR"

# Configurer le système RAG
echo "🧠 Configuration du système RAG..."
python manage.py setup_rag --vectorize || echo "⚠️  Erreur lors de la configuration RAG"

# Créer un superutilisateur si il n'existe pas
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sar.sn', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

echo "✅ Backend Django prêt!"
echo "🌐 Serveur démarré sur http://0.0.0.0:8000"

# Démarrer le serveur Django
exec python manage.py runserver 0.0.0.0:8000
