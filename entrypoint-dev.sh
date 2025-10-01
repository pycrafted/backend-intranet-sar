#!/bin/bash
set -e

echo "🚀 Démarrage ULTRA-RAPIDE du backend Django SAR..."

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente de PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "   PostgreSQL n'est pas encore prêt, attente..."
  sleep 2
done
echo "✅ PostgreSQL est prêt!"

# Installer les dépendances RAG au runtime (lazy loading)
echo "🧠 Installation des dépendances RAG au runtime..."
pip install --no-cache-dir \
    sentence-transformers==2.7.0 \
    faiss-cpu==1.7.4 \
    langchain==0.1.0 \
    langchain-community==0.0.10 \
    pgvector==0.2.4 \
    numpy==1.24.3 \
    huggingface-hub==0.19.4

# Appliquer les migrations
echo "🔄 Application des migrations Django..."
python manage.py migrate

# Collecter les fichiers statiques
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Importer le dataset SAR si il n'existe pas
echo "📊 Vérification du dataset SAR..."
if [ ! -f "data/sar_official_dataset.csv" ]; then
    echo "⚠️  Dataset SAR non trouvé, création d'un dataset de test..."
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
