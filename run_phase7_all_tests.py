#!/usr/bin/env python
"""
Phase 7 - Script Maître pour Tous les Tests
Exécute tous les tests exhaustifs du chatbot RAG.
"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Any

class Phase7TestRunner:
    """Exécuteur de tous les tests Phase 7"""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_suites = []
        self.overall_results = {}
        
    def log_suite(self, suite_name: str, success: bool, details: str = "", duration: float = 0):
        """Enregistre un résultat de suite de tests"""
        result = {
            'suite_name': suite_name,
            'success': success,
            'details': details,
            'duration_seconds': round(duration, 2),
            'timestamp': datetime.now().isoformat()
        }
        self.test_suites.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"[SUITE] {status}: {suite_name} ({duration:.1f}s)")
        if details:
            print(f"    {details}")
    
    def run_test_suite(self, script_name: str, suite_name: str, timeout: int = 300):
        """Exécute une suite de tests"""
        print(f"\n{'='*60}")
        print(f"EXÉCUTION: {suite_name}")
        print(f"{'='*60}")
        
        try:
            start_time = time.time()
            
            # Exécuter le script de test
            result = subprocess.run([
                sys.executable, script_name
            ], capture_output=True, text=True, timeout=timeout)
            
            duration = time.time() - start_time
            
            # Analyser les résultats
            success = result.returncode == 0
            
            # Afficher la sortie
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            self.log_suite(suite_name, success, 
                          f"Return code: {result.returncode}", duration)
            return success
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_suite(suite_name, False, f"Timeout after {timeout}s", duration)
            return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_suite(suite_name, False, f"Error: {e}", duration)
            return False
    
    def check_prerequisites(self):
        """Vérifie les prérequis"""
        print("VÉRIFICATION DES PRÉREQUIS")
        print("=" * 40)
        
        # Vérifier que les scripts existent
        required_scripts = [
            'test_chatbot_comprehensive.py',
            'test_user_scenarios.py',
            'test_performance_stress.py',
            'test_phase6_simple.py'
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if not os.path.exists(script):
                missing_scripts.append(script)
        
        if missing_scripts:
            print(f"ERREUR: Scripts manquants: {missing_scripts}")
            return False
        
        print("OK: Tous les scripts de test sont presents")
        return True
    
    def run_all_tests(self):
        """Exécute tous les tests Phase 7"""
        print("PHASE 7 - TESTS EXHAUSTIFS DU CHATBOT RAG")
        print("=" * 60)
        print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Vérifier les prérequis
        if not self.check_prerequisites():
            print("ERREUR: Prérequis non satisfaits")
            return False
        
        # Définir les suites de tests
        test_suites = [
            {
                'script': 'test_phase6_simple.py',
                'name': 'Tests Phase 6 - Optimisations',
                'timeout': 120,
                'critical': True
            },
            {
                'script': 'test_chatbot_comprehensive.py',
                'name': 'Tests Exhaustifs du Chatbot',
                'timeout': 300,
                'critical': True
            },
            {
                'script': 'test_user_scenarios.py',
                'name': 'Tests des Scénarios Utilisateur',
                'timeout': 180,
                'critical': True
            },
            {
                'script': 'test_performance_stress.py',
                'name': 'Tests de Performance et Charge',
                'timeout': 300,
                'critical': True
            }
        ]
        
        # Exécuter les suites de tests
        total_suites = len(test_suites)
        passed_suites = 0
        critical_failures = 0
        
        for suite in test_suites:
            success = self.run_test_suite(
                suite['script'], 
                suite['name'], 
                suite['timeout']
            )
            
            if success:
                passed_suites += 1
            elif suite['critical']:
                critical_failures += 1
        
        # Calculer les statistiques
        total_duration = time.time() - self.start_time
        success_rate = (passed_suites / total_suites) * 100
        
        # Afficher le résumé final
        print("\n" + "=" * 60)
        print("RÉSUMÉ FINAL PHASE 7")
        print("=" * 60)
        print(f"Suites de tests: {passed_suites}/{total_suites} ({success_rate:.1f}%)")
        print(f"Durée totale: {total_duration:.1f}s")
        print(f"Échecs critiques: {critical_failures}")
        
        # Déterminer le statut global
        if critical_failures == 0 and success_rate >= 90:
            status = "EXCELLENT"
            message = "EXCELLENT: Le chatbot est pret pour la production !"
            overall_success = True
        elif critical_failures == 0 and success_rate >= 80:
            status = "BON"
            message = "BON: Le chatbot fonctionne bien avec quelques ameliorations mineures"
            overall_success = True
        elif critical_failures <= 1 and success_rate >= 70:
            status = "ACCEPTABLE"
            message = "ACCEPTABLE: Le chatbot fonctionne mais necessite des ameliorations"
            overall_success = False
        else:
            status = "CRITIQUE"
            message = "CRITIQUE: Le chatbot necessite des corrections importantes"
            overall_success = False
        
        print(f"\nSTATUT GLOBAL: {status}")
        print(f"MESSAGE: {message}")
        
        # Sauvegarder les résultats
        self.save_overall_results(overall_success, success_rate, critical_failures)
        
        return overall_success
    
    def save_overall_results(self, success: bool, success_rate: float, critical_failures: int):
        """Sauvegarde les résultats globaux"""
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'total_duration_seconds': time.time() - self.start_time,
                'overall_success': success,
                'success_rate_percent': success_rate,
                'critical_failures': critical_failures,
                'test_suites': self.test_suites,
                'summary': {
                    'total_suites': len(self.test_suites),
                    'passed_suites': sum(1 for s in self.test_suites if s['success']),
                    'failed_suites': sum(1 for s in self.test_suites if not s['success']),
                }
            }
            
            with open('phase7_overall_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 Résultats globaux sauvegardés dans phase7_overall_results.json")
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde résultats globaux: {e}")
    
    def generate_test_report(self):
        """Génère un rapport de test détaillé"""
        try:
            report = f"""
# RAPPORT DE TESTS PHASE 7 - CHATBOT RAG
## Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé Exécutif
- **Durée totale**: {time.time() - self.start_time:.1f}s
- **Suites de tests**: {len(self.test_suites)}
- **Taux de réussite**: {sum(1 for s in self.test_suites if s['success']) / len(self.test_suites) * 100:.1f}%

## Détail des Suites de Tests
"""
            
            for suite in self.test_suites:
                status = "✅ PASS" if suite['success'] else "❌ FAIL"
                report += f"""
### {suite['suite_name']}
- **Statut**: {status}
- **Durée**: {suite['duration_seconds']}s
- **Détails**: {suite['details']}
- **Timestamp**: {suite['timestamp']}
"""
            
            report += f"""
## Recommandations

### Si tous les tests passent (90%+):
- Le chatbot est prêt pour la production
- Mettre en place un monitoring continu
- Planifier des tests de régression réguliers

### Si la plupart des tests passent (80-89%):
- Corriger les problèmes identifiés
- Re-tester les composants défaillants
- Considérer un déploiement en bêta

### Si certains tests échouent (70-79%):
- Analyser en détail les échecs
- Prioriser les corrections critiques
- Re-tester après corrections

### Si beaucoup de tests échouent (<70%):
- Revoir l'architecture du système
- Corriger les problèmes fondamentaux
- Re-tester complètement

## Fichiers de Résultats
- `phase7_overall_results.json`: Résultats globaux
- `chatbot_test_results.json`: Tests exhaustifs
- `user_scenario_results.json`: Scénarios utilisateur
- `performance_test_results.json`: Tests de performance
- `phase6_test_results.json`: Tests Phase 6
"""
            
            with open('phase7_test_report.md', 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"📄 Rapport détaillé généré: phase7_test_report.md")
            
        except Exception as e:
            print(f"⚠️ Erreur génération rapport: {e}")

def main():
    """Fonction principale"""
    runner = Phase7TestRunner()
    success = runner.run_all_tests()
    runner.generate_test_report()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
