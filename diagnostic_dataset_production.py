#!/usr/bin/env python3
"""
Diagnostic du chargement du dataset en production
"""

import os
import sys
import django
import csv
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings_render')
django.setup()

def check_dataset_file():
    """Vérifier l'existence et la taille du fichier dataset"""
    print("🔍 Vérification du fichier dataset...")
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'sar_official_dataset.csv')
    
    if os.path.exists(dataset_path):
        file_size = os.path.getsize(dataset_path)
        print(f"   ✅ Fichier dataset trouvé: {dataset_path}")
        print(f"   ✅ Taille: {file_size:,} octets")
        return True
    else:
        print(f"   ❌ Fichier dataset non trouvé: {dataset_path}")
        return False

def check_dataset_content():
    """Vérifier le contenu du dataset"""
    print("\n🔍 Vérification du contenu du dataset...")
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'sar_official_dataset.csv')
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
        print(f"   ✅ Nombre de lignes: {len(rows)}")
        
        # Vérifier des questions spécifiques
        test_questions = [
            "Qui est l'actuel Directeur général de la SAR ?",
            "Où se trouve la SAR ?",
            "Quelle est la fonction du wharf opéré par la SAR ?"
        ]
        
        for question in test_questions:
            found = False
            for row in rows:
                if question.lower() in row.get('question', '').lower():
                    print(f"   ✅ Question trouvée: '{question}'")
                    print(f"      Réponse: {row.get('answer', '')[:100]}...")
                    found = True
                    break
            
            if not found:
                print(f"   ❌ Question non trouvée: '{question}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la lecture: {e}")
        return False

def check_mai_service():
    """Vérifier le service MAI"""
    print("\n🔍 Vérification du service MAI...")
    
    try:
        from mai.services import MAIService
        
        # Initialiser le service
        mai_service = MAIService()
        print(f"   ✅ MAIService initialisé")
        print(f"   ✅ Dataset chargé: {len(mai_service.qa_pairs)} questions")
        
        # Test de recherche
        test_questions = [
            "Qui est l'actuel Directeur général de la SAR ?",
            "Où se trouve la SAR ?",
            "Quelle est la fonction du wharf opéré par la SAR ?"
        ]
        
        for question in test_questions:
            result = mai_service.search_answer(question, threshold=0.1)
            if result:
                print(f"   ✅ Question: '{question}'")
                print(f"      Réponse: {result['answer'][:100]}...")
                print(f"      Similarité: {result['similarity']:.3f}")
            else:
                print(f"   ❌ Question non trouvée: '{question}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur MAIService: {e}")
        return False

def check_database_data():
    """Vérifier les données en base"""
    print("\n🔍 Vérification des données en base...")
    
    try:
        from mai.models import DocumentEmbedding
        
        # Compter les documents
        count = DocumentEmbedding.objects.count()
        print(f"   ✅ Documents en base: {count}")
        
        if count > 0:
            # Vérifier quelques documents
            docs = DocumentEmbedding.objects.all()[:5]
            for doc in docs:
                print(f"   📄 Document: {doc.content[:100]}...")
        
        return count > 0
        
    except Exception as e:
        print(f"   ❌ Erreur base de données: {e}")
        return False

def main():
    """Fonction principale de diagnostic"""
    print("🧪 DIAGNOSTIC DU DATASET EN PRODUCTION")
    print("=" * 60)
    
    tests = [
        ("Fichier Dataset", check_dataset_file),
        ("Contenu Dataset", check_dataset_content),
        ("Service MAI", check_mai_service),
        ("Base de Données", check_database_data),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DU DIAGNOSTIC")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS - Dataset correctement chargé!")
        return True
    else:
        print("⚠️  Certains tests ont échoué - Problème de chargement du dataset")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
