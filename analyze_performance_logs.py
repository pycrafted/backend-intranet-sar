#!/usr/bin/env python
"""
Script pour analyser les logs de performance et générer un rapport
"""
import re
import sys
from collections import defaultdict
from datetime import datetime

def parse_log_line(line):
    """Parse une ligne de log de performance"""
    # Format: [PERF] METHOD /path | Temps total: XXXms | SQL: N requêtes (XXXms) | Traitement: XXXms | Status: XXX
    pattern = r'\[PERF\]\s+(\w+)\s+([^\s]+)\s+\|\s+Temps total:\s+([\d.]+)ms\s+\|\s+SQL:\s+(\d+)\s+requêtes\s+\(([\d.]+)ms\)\s+\|\s+Traitement:\s+([\d.]+)ms\s+\|\s+Status:\s+(\d+)'
    match = re.search(pattern, line)
    
    if match:
        return {
            'method': match.group(1),
            'path': match.group(2),
            'total_time': float(match.group(3)),
            'sql_queries': int(match.group(4)),
            'sql_time': float(match.group(5)),
            'processing_time': float(match.group(6)),
            'status': int(match.group(7))
        }
    return None

def analyze_logs(log_file=None):
    """Analyse les logs de performance"""
    stats = {
        'total_requests': 0,
        'slow_requests': [],  # > 1s
        'very_slow_requests': [],  # > 2s
        'high_sql_queries': [],  # > 10 requêtes
        'paths': defaultdict(list),
        'avg_times': {
            'total': [],
            'sql': [],
            'processing': []
        }
    }
    
    # Lire depuis stdin ou fichier
    if log_file:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    
    for line in lines:
        data = parse_log_line(line)
        if not data:
            continue
        
        stats['total_requests'] += 1
        stats['avg_times']['total'].append(data['total_time'])
        stats['avg_times']['sql'].append(data['sql_time'])
        stats['avg_times']['processing'].append(data['processing_time'])
        stats['paths'][data['path']].append(data)
        
        # Requêtes lentes
        if data['total_time'] > 2000:
            stats['very_slow_requests'].append(data)
        elif data['total_time'] > 1000:
            stats['slow_requests'].append(data)
        
        # Trop de requêtes SQL
        if data['sql_queries'] > 10:
            stats['high_sql_queries'].append(data)
    
    return stats

def print_report(stats):
    """Affiche le rapport d'analyse"""
    print("=" * 80)
    print("RAPPORT D'ANALYSE DES PERFORMANCES")
    print("=" * 80)
    print()
    
    if stats['total_requests'] == 0:
        print("Aucune requête trouvée dans les logs.")
        return
    
    # Statistiques générales
    print("📊 STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    print(f"Total de requêtes analysées: {stats['total_requests']}")
    
    avg_total = sum(stats['avg_times']['total']) / len(stats['avg_times']['total'])
    avg_sql = sum(stats['avg_times']['sql']) / len(stats['avg_times']['sql'])
    avg_processing = sum(stats['avg_times']['processing']) / len(stats['avg_times']['processing'])
    
    print(f"Temps moyen total: {avg_total:.2f}ms")
    print(f"Temps moyen SQL: {avg_sql:.2f}ms")
    print(f"Temps moyen traitement: {avg_processing:.2f}ms")
    print()
    
    # Requêtes lentes
    if stats['slow_requests']:
        print("🟡 REQUÊTES LENTES (> 1s)")
        print("-" * 80)
        for req in sorted(stats['slow_requests'], key=lambda x: x['total_time'], reverse=True)[:10]:
            print(f"  {req['method']} {req['path']}")
            print(f"    Temps: {req['total_time']:.2f}ms | SQL: {req['sql_queries']} ({req['sql_time']:.2f}ms) | Status: {req['status']}")
        print()
    
    if stats['very_slow_requests']:
        print("🔴 REQUÊTES TRÈS LENTES (> 2s)")
        print("-" * 80)
        for req in sorted(stats['very_slow_requests'], key=lambda x: x['total_time'], reverse=True):
            print(f"  {req['method']} {req['path']}")
            print(f"    Temps: {req['total_time']:.2f}ms | SQL: {req['sql_queries']} ({req['sql_time']:.2f}ms) | Status: {req['status']}")
        print()
    
    # Pages avec trop de requêtes SQL
    if stats['high_sql_queries']:
        print("⚠️  PAGES AVEC TROP DE REQUÊTES SQL (> 10)")
        print("-" * 80)
        for req in sorted(stats['high_sql_queries'], key=lambda x: x['sql_queries'], reverse=True)[:10]:
            print(f"  {req['method']} {req['path']}")
            print(f"    Requêtes SQL: {req['sql_queries']} | Temps SQL: {req['sql_time']:.2f}ms")
        print()
    
    # Pages les plus fréquentes
    print("📈 PAGES LES PLUS FRÉQUENTES")
    print("-" * 80)
    sorted_paths = sorted(stats['paths'].items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for path, requests in sorted_paths:
        avg_time = sum(r['total_time'] for r in requests) / len(requests)
        avg_sql = sum(r['sql_queries'] for r in requests) / len(requests)
        print(f"  {path}")
        print(f"    Appels: {len(requests)} | Temps moyen: {avg_time:.2f}ms | SQL moyen: {avg_sql:.1f}")
    print()
    
    # Recommandations
    print("💡 RECOMMANDATIONS")
    print("-" * 80)
    if stats['slow_requests']:
        print("  • Optimiser les pages lentes identifiées ci-dessus")
    if stats['high_sql_queries']:
        print("  • Utiliser select_related() et prefetch_related() pour réduire les requêtes SQL")
    if avg_total > 1000:
        print("  • Mettre en cache les données fréquemment accédées")
    if avg_sql > 200:
        print("  • Optimiser les requêtes SQL et ajouter des index")
    print()
    
    print("=" * 80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyse les logs de performance')
    parser.add_argument('--file', '-f', help='Fichier de log à analyser (sinon lit depuis stdin)')
    args = parser.parse_args()
    
    stats = analyze_logs(args.file)
    print_report(stats)







