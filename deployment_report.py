#!/usr/bin/env python
"""
Rapport de déploiement en production pour la Phase 4.
Génère un rapport complet du déploiement.
"""
import os
import sys
import django
import time
import json
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'master.settings')
django.setup()

from mai.deployment_manager import deployment_manager
from mai.monitoring_dashboard import monitoring_dashboard
from mai.vector_search_service import vector_search_service
from mai.services import MAIService
from mai.models import RAGSearchLog, DocumentEmbedding

def generate_deployment_report():
    """Génère un rapport de déploiement complet"""
    print("=== RAPPORT DEPLOIEMENT PRODUCTION PHASE 4 ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Statut du déploiement
    print("\n[1] STATUT DU DEPLOIEMENT")
    deployment_status = deployment_manager.get_deployment_status()
    print(f"  Phase actuelle: {deployment_status.get('phase', 'N/A')}")
    print(f"  Statut: {deployment_status.get('status', 'N/A')}")
    print(f"  Durée écoulée: {deployment_status.get('elapsed_hours', 0):.1f}h")
    
    # 2. Métriques de performance
    print("\n[2] METRIQUES DE PERFORMANCE")
    metrics = monitoring_dashboard.get_real_time_metrics()
    
    base_metrics = metrics.get('base_metrics', {})
    print(f"  Recherches totales: {base_metrics.get('total_searches', 0)}")
    print(f"  Taux de succès: {base_metrics.get('success_rate', 0):.1f}%")
    print(f"  Taux d'erreur: {base_metrics.get('error_rate', 0):.1f}%")
    
    performance_metrics = metrics.get('performance_metrics', {})
    print(f"  Temps moyen: {performance_metrics.get('avg_response_time_ms', 0):.1f}ms")
    print(f"  Temps max: {performance_metrics.get('max_response_time_ms', 0):.1f}ms")
    print(f"  Temps min: {performance_metrics.get('min_response_time_ms', 0):.1f}ms")
    
    # 3. Métriques système
    print("\n[3] METRIQUES SYSTEME")
    system_metrics = metrics.get('system_metrics', {})
    print(f"  CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
    print(f"  Mémoire: {system_metrics.get('memory_percent', 0):.1f}%")
    print(f"  Disque: {system_metrics.get('disk_percent', 0):.1f}%")
    
    # 4. Alertes
    print("\n[4] ALERTES")
    alerts = metrics.get('alerts', [])
    print(f"  Alertes totales: {len(alerts)}")
    
    critical_alerts = [a for a in alerts if a.get('type') == 'critical']
    warning_alerts = [a for a in alerts if a.get('type') == 'warning']
    
    print(f"  Alertes critiques: {len(critical_alerts)}")
    print(f"  Alertes avertissement: {len(warning_alerts)}")
    
    for i, alert in enumerate(alerts, 1):
        print(f"    {i}. {alert.get('message', 'N/A')} ({alert.get('type', 'N/A')})")
    
    # 5. Santé du système
    print("\n[5] SANTE DU SYSTEME")
    health = monitoring_dashboard.get_health_check()
    print(f"  Statut global: {health.get('overall_status', 'N/A')}")
    
    checks = health.get('checks', {})
    for component, check in checks.items():
        status = check.get('status', 'unknown')
        print(f"  {component}: {status}")
    
    # 6. Données vectorielles
    print("\n[6] DONNEES VECTORIELLES")
    total_docs = DocumentEmbedding.objects.count()
    sar_docs = DocumentEmbedding.objects.filter(content_type='qa_pair').count()
    print(f"  Documents total: {total_docs}")
    print(f"  Documents SAR: {sar_docs}")
    print(f"  Couverture: {(sar_docs/total_docs*100):.1f}%")
    
    # 7. Tests de performance
    print("\n[7] TESTS DE PERFORMANCE")
    test_queries = [
        "Quelle est la date d'inauguration de la SAR ?",
        "Quelle est la capacité de la SAR ?",
        "Quels sont les produits de la SAR ?"
    ]
    
    vector_times = []
    heuristic_times = []
    
    for query in test_queries:
        # Test vectoriel
        start_time = time.time()
        vector_results = vector_search_service.search_similar(query, limit=3, threshold=0.4)
        vector_time = time.time() - start_time
        vector_times.append(vector_time)
        
        # Test heuristique
        start_time = time.time()
        mai_service = MAIService()
        heuristic_context = mai_service.get_context_for_question(query)
        heuristic_time = time.time() - start_time
        heuristic_times.append(heuristic_time)
    
    avg_vector_time = sum(vector_times) / len(vector_times)
    avg_heuristic_time = sum(heuristic_times) / len(heuristic_times)
    
    print(f"  Temps moyen vectoriel: {avg_vector_time*1000:.1f}ms")
    print(f"  Temps moyen heuristique: {avg_heuristic_time*1000:.1f}ms")
    print(f"  Ratio de performance: {avg_heuristic_time/avg_vector_time:.1f}x")
    
    # 8. Recommandations
    print("\n[8] RECOMMANDATIONS")
    recommendations = deployment_manager.get_deployment_recommendations()
    print(f"  Recommandations: {len(recommendations)}")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")
    
    # 9. Résumé
    print("\n[9] RESUME")
    print("  ==========")
    print(f"  Phase: {deployment_status.get('phase', 'N/A')}")
    print(f"  Statut: {deployment_status.get('status', 'N/A')}")
    print(f"  Recherches: {base_metrics.get('total_searches', 0)}")
    print(f"  Succès: {base_metrics.get('success_rate', 0):.1f}%")
    print(f"  Temps moyen: {performance_metrics.get('avg_response_time_ms', 0):.1f}ms")
    print(f"  Santé: {health.get('overall_status', 'N/A')}")
    print(f"  Alertes: {len(alerts)}")
    
    # 10. Conclusion
    print("\n[10] CONCLUSION")
    print("  ==============")
    
    success_rate = base_metrics.get('success_rate', 0)
    avg_response_time = performance_metrics.get('avg_response_time_ms', 0)
    overall_status = health.get('overall_status', 'unknown')
    
    if success_rate >= 90 and avg_response_time < 1000 and overall_status == 'healthy':
        print("  DEPLOIEMENT REUSSI - Systeme operationnel")
        print("  - Taux de succes excellent")
        print("  - Performances optimales")
        print("  - Systeme en bonne sante")
    elif success_rate >= 80 and avg_response_time < 2000:
        print("  DEPLOIEMENT PARTIELLEMENT REUSSI - Surveillance requise")
        print("  - Taux de succes acceptable")
        print("  - Performances correctes")
        print("  - Surveillance recommandee")
    else:
        print("  DEPLOIEMENT PROBLEMATIQUE - Intervention requise")
        print("  - Taux de succes faible")
        print("  - Performances degradees")
        print("  - Intervention requise")
    
    print(f"\nRapport genere le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=== FIN DU RAPPORT ===")

if __name__ == '__main__':
    generate_deployment_report()
