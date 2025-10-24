#!/bin/bash
# Script d'installation des dépendances Phase 6
# Installe Redis et les dépendances Python nécessaires

echo "🚀 Installation des dépendances Phase 6 - Optimisations Avancées"
echo "=================================================================="

# Vérifier si on est sur WSL
if grep -q Microsoft /proc/version; then
    echo "✅ WSL détecté - Installation Redis sur Ubuntu"
    
    # Mettre à jour les paquets
    echo "📦 Mise à jour des paquets..."
    sudo apt update
    
    # Installer Redis si pas déjà installé
    if ! command -v redis-server &> /dev/null; then
        echo "🔧 Installation de Redis..."
        sudo apt install redis-server -y
        
        # Démarrer Redis
        echo "🚀 Démarrage de Redis..."
        sudo service redis-server start
        
        # Vérifier que Redis fonctionne
        if redis-cli ping | grep -q PONG; then
            echo "✅ Redis fonctionne correctement"
        else
            echo "❌ Erreur: Redis ne répond pas"
            exit 1
        fi
    else
        echo "✅ Redis déjà installé"
    fi
    
    # Installer les dépendances Python
    echo "🐍 Installation des dépendances Python..."
    pip install django-redis==5.4.0
    pip install redis==5.0.1
    pip install redis-py-cluster==2.1.3
    
else
    echo "⚠️ WSL non détecté - Installation manuelle requise"
    echo "Veuillez installer Redis manuellement sur votre système"
fi

# Vérifier l'installation
echo ""
echo "🔍 Vérification de l'installation..."

# Test Redis
if redis-cli ping | grep -q PONG; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: ÉCHEC"
fi

# Test Python packages
python -c "import redis; print('✅ redis: OK')" 2>/dev/null || echo "❌ redis: ÉCHEC"
python -c "import django_redis; print('✅ django-redis: OK')" 2>/dev/null || echo "❌ django-redis: ÉCHEC"

echo ""
echo "🎉 Installation terminée !"
echo "Vous pouvez maintenant exécuter: python test_phase6_optimizations.py"

