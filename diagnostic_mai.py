#!/usr/bin/env python
"""
Script de diagnostic pour le système MAI.
Teste le chargement du dataset, le filtrage SAR et la recherche.
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from mai.services import MAIService

def test_dataset_loading():
    """Teste le chargement du dataset"""
    print("=== TEST CHARGEMENT DATASET ===")
    service = MAIService()
    print(f"Nombre de questions chargées: {service.get_question_count()}")
    
    if service.get_question_count() == 0:
        print("❌ ERREUR: Aucune question chargée!")
        return False
    
    print("✅ Dataset chargé avec succès")
    return True

def test_sar_filtering():
    """Teste le filtrage SAR"""
    print("\n=== TEST FILTRAGE SAR ===")
    service = MAIService()
    
    test_questions = [
        "L'objet d'incertitude est l'élément, la situation ou l'événement qui présente un risque ou une opportunité pour l'organisation.",
        "accéder au bilan des risques dans QUALIPRO",
        "Comment est calculé le score d'un risque ?",
        "Quelles informations trouve-t-on dans l'agenda d'un utilisateur ?",
        "Qu'est-ce que la SAR ?",
        "Comment fonctionne QUALIPRO ?"
    ]
    
    for question in test_questions:
        is_sar = service.is_question_about_sar(question)
        print(f"Question: '{question[:50]}...'")
        print(f"SAR: {is_sar}")
        print("-" * 50)

def test_similarity_search():
    """Teste la recherche de similarité"""
    print("\n=== TEST RECHERCHE SIMILARITÉ ===")
    service = MAIService()
    
    test_questions = [
        "L'objet d'incertitude est l'élément, la situation ou l'événement qui présente un risque ou une opportunité pour l'organisation.",
        "accéder au bilan des risques dans QUALIPRO",
        "Comment est calculé le score d'un risque ?",
        "Quelles informations trouve-t-on dans l'agenda d'un utilisateur ?"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: '{question}'")
        
        # Test avec différents seuils
        for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
            result = service.search_answer(question, threshold=threshold)
            if result:
                print(f"  Seuil {threshold}: TROUVÉ - Similarité: {result['similarity']:.3f}")
                print(f"  Réponse: {result['answer'][:100]}...")
                break
            else:
                print(f"  Seuil {threshold}: Non trouvé")
        else:
            print("  ❌ Aucune correspondance trouvée même avec seuil 0.1")

def test_exact_matches():
    """Teste les correspondances exactes du dataset"""
    print("\n=== TEST CORRESPONDANCES EXACTES ===")
    service = MAIService()
    
    exact_questions = [
        "Que signifie l'expression 'objet d'incertitude' ?",
        "Comment peut-on accéder au bilan des risques dans QUALIPRO ?",
        "Comment est calculé le score d'un risque ?",
        "Quelles informations trouve-t-on dans l'agenda d'un utilisateur ?"
    ]
    
    for question in exact_questions:
        print(f"\nQuestion exacte: '{question}'")
        result = service.search_answer(question, threshold=0.1)
        if result:
            print(f"✅ TROUVÉ - Similarité: {result['similarity']:.3f}")
            print(f"Réponse: {result['answer']}")
        else:
            print("❌ NON TROUVÉ")

def test_normalization():
    """Teste la normalisation du texte"""
    print("\n=== TEST NORMALISATION ===")
    service = MAIService()
    
    test_texts = [
        "L'objet d'incertitude est l'élément, la situation ou l'événement qui présente un risque ou une opportunité pour l'organisation.",
        "accéder au bilan des risques dans QUALIPRO",
        "Comment est calculé le score d'un risque ?",
        "Quelles informations trouve-t-on dans l'agenda d'un utilisateur ?"
    ]
    
    for text in test_texts:
        normalized = service._normalize_text(text)
        print(f"Original: {text[:50]}...")
        print(f"Normalisé: {normalized[:50]}...")
        print("-" * 50)

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC SYSTÈME MAI")
    print("=" * 50)
    
    # Test 1: Chargement du dataset
    if not test_dataset_loading():
        print("❌ ÉCHEC: Dataset non chargé")
        return
    
    # Test 2: Filtrage SAR
    test_sar_filtering()
    
    # Test 3: Normalisation
    test_normalization()
    
    # Test 4: Correspondances exactes
    test_exact_matches()
    
    # Test 5: Recherche de similarité
    test_similarity_search()
    
    print("\n🎯 DIAGNOSTIC TERMINÉ")

if __name__ == "__main__":
    main()
