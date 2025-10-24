#!/usr/bin/env python3
"""
Diagnostic complet pour comparer le comportement local vs production
"""

import os
import sys
import django
import csv
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

def test_question_processing():
    """Test du traitement de la question problématique"""
    print("🔍 Test du traitement de la question 'qui est le dg de la sar'...")
    
    from mai.services import MAIService
    
    mai_service = MAIService()
    
    question = "qui est le dg de la sar"
    
    # Test de normalisation
    normalized = mai_service._normalize_text(question)
    print(f"   Question originale: '{question}'")
    print(f"   Question normalisée: '{normalized}'")
    
    # Test de recherche avec différents seuils
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("   Test avec différents seuils:")
    for threshold in thresholds:
        result = mai_service.search_answer(question, threshold=threshold)
        if result:
            print(f"   ✅ Seuil {threshold}: {result['answer'][:50]}... (similarité: {result['similarity']:.3f})")
        else:
            print(f"   ❌ Seuil {threshold}: Aucune réponse")
    
    return True

def test_dataset_questions():
    """Test des questions similaires dans le dataset"""
    print("\n🔍 Test des questions similaires dans le dataset...")
    
    from mai.services import MAIService
    
    mai_service = MAIService()
    
    # Rechercher toutes les questions contenant "directeur" ou "dg"
    director_questions = []
    
    for qa_pair in mai_service.qa_pairs:
        question = qa_pair['question'].lower()
        if 'directeur' in question or 'dg' in question:
            director_questions.append(qa_pair)
    
    print(f"   Questions trouvées contenant 'directeur' ou 'dg': {len(director_questions)}")
    
    for i, qa_pair in enumerate(director_questions[:5]):  # Afficher les 5 premières
        print(f"   {i+1}. {qa_pair['question']}")
        print(f"      Réponse: {qa_pair['answer'][:100]}...")
    
    return True

def test_similarity_calculation():
    """Test du calcul de similarité avec la question problématique"""
    print("\n🔍 Test du calcul de similarité...")
    
    from mai.services import MAIService
    
    mai_service = MAIService()
    
    question = "qui est le dg de la sar"
    
    # Trouver la question de référence dans le dataset
    reference_question = None
    for qa_pair in mai_service.qa_pairs:
        if "directeur général" in qa_pair['question'].lower():
            reference_question = qa_pair['question']
            break
    
    if reference_question:
        print(f"   Question de référence: '{reference_question}'")
        
        # Calculer la similarité
        similarity = mai_service._calculate_similarity(question, reference_question)
        print(f"   Similarité calculée: {similarity:.3f}")
        
        # Test de normalisation des deux questions
        q1_norm = mai_service._normalize_text(question)
        q2_norm = mai_service._normalize_text(reference_question)
        
        print(f"   Question normalisée: '{q1_norm}'")
        print(f"   Référence normalisée: '{q2_norm}'")
        
        # Vérifier les mots communs
        q1_words = set(q1_norm.split())
        q2_words = set(q2_norm.split())
        common_words = q1_words.intersection(q2_words)
        
        print(f"   Mots communs: {common_words}")
        print(f"   Nombre de mots communs: {len(common_words)}")
        
    else:
        print("   ❌ Aucune question de référence trouvée")
    
    return True

def test_configuration_differences():
    """Test des différences de configuration"""
    print("\n🔍 Test des différences de configuration...")
    
    from django.conf import settings
    
    # Vérifier les paramètres RAG
    rag_config = getattr(settings, 'RAG_CONFIG', {})
    print(f"   RAG_CONFIG: {rag_config}")
    
    # Vérifier les paramètres de migration
    migration_config = getattr(settings, 'RAG_MIGRATION_CONFIG', {})
    print(f"   RAG_MIGRATION_CONFIG: {migration_config}")
    
    # Vérifier le seuil de similarité par défaut
    default_threshold = getattr(settings, 'DEFAULT_SIMILARITY_THRESHOLD', 0.3)
    print(f"   Seuil de similarité par défaut: {default_threshold}")
    
    return True

def test_maiservice_initialization():
    """Test de l'initialisation du MAIService"""
    print("\n🔍 Test de l'initialisation du MAIService...")
    
    from mai.services import MAIService
    
    try:
        mai_service = MAIService()
        print(f"   ✅ MAIService initialisé avec succès")
        print(f"   ✅ Nombre de questions chargées: {len(mai_service.qa_pairs)}")
        
        # Vérifier que le dataset contient la question sur le DG
        dg_question_found = False
        for qa_pair in mai_service.qa_pairs:
            if "directeur général" in qa_pair['question'].lower() and "mamadou abib diop" in qa_pair['answer'].lower():
                dg_question_found = True
                print(f"   ✅ Question DG trouvée: '{qa_pair['question']}'")
                print(f"   ✅ Réponse: '{qa_pair['answer']}'")
                break
        
        if not dg_question_found:
            print("   ❌ Question DG non trouvée dans le dataset")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'initialisation: {e}")
        return False

def test_specific_question_search():
    """Test de recherche spécifique pour la question problématique"""
    print("\n🔍 Test de recherche spécifique...")
    
    from mai.services import MAIService
    
    mai_service = MAIService()
    
    question = "qui est le dg de la sar"
    
    # Recherche avec seuil très bas
    result = mai_service.search_answer(question, threshold=0.01)
    
    if result:
        print(f"   ✅ Réponse trouvée avec seuil 0.01:")
        print(f"      Question: {result['question']}")
        print(f"      Réponse: {result['answer']}")
        print(f"      Similarité: {result['similarity']:.3f}")
    else:
        print("   ❌ Aucune réponse trouvée même avec seuil 0.01")
        
        # Afficher les similarités des 5 meilleures questions
        print("   Top 5 des similarités:")
        similarities = []
        
        for qa_pair in mai_service.qa_pairs:
            sim = mai_service._calculate_similarity(question, qa_pair['question'])
            similarities.append((qa_pair['question'], sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        for i, (q, sim) in enumerate(similarities[:5]):
            print(f"      {i+1}. {sim:.3f} - {q[:80]}...")
    
    return True

def main():
    """Fonction principale de diagnostic"""
    print("🧪 DIAGNOSTIC LOCAL VS PRODUCTION")
    print("=" * 60)
    
    tests = [
        ("Traitement Question", test_question_processing),
        ("Questions Dataset", test_dataset_questions),
        ("Calcul Similarité", test_similarity_calculation),
        ("Configuration", test_configuration_differences),
        ("Initialisation MAI", test_maiservice_initialization),
        ("Recherche Spécifique", test_specific_question_search),
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
        print("🎉 TOUS LES TESTS RÉUSSIS - Comportement local normal!")
        return True
    else:
        print("⚠️  Certains tests ont échoué - Problème identifié")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

