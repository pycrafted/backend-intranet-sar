#!/usr/bin/env python
"""
Script de monitoring de production pour le système RAG SAR.
Surveille en temps réel les performances et la santé du système.
"""
import os
import sys
import time
import json
import requests
import psutil
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any

class ProductionMonitor:
    """Moniteur de production pour le système RAG SAR"""
    
    def __init__(self):
        import os
        from decouple import config
        # ⚠️ Aucune valeur par défaut pour la sécurité - doit venir du .env
        self.backend_url = config('BASE_URL')
        self.monitoring_data = []
        self.alerts = []
        self.start_time = time.time()
        
        # Configuration des seuils
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time_ms': 2000,
            'error_rate_percent': 5,
            'success_rate_percent': 95,
        }
        
        # Configuration des alertes
        self.alert_config = {
            'email_enabled': False,
            'email_smtp_server': 'smtp.gmail.com',
            'email_smtp_port': 587,
            'email_username': '',
            'email_password': '',
            'email_recipients': ['admin@intranet-sar.com'],
            'slack_webhook': None,
        }
    
    def log_metric(self, metric_name: str, value: float, unit: str = "", status: str = "OK"):
        """Enregistre une métrique"""
        metric = {
            'timestamp': datetime.now().isoformat(),
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'status': status
        }
        self.monitoring_data.append(metric)
        
        status_icon = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
        print(f"{status_icon} {metric_name}: {value}{unit}")
    
    def check_system_metrics(self):
        """Vérifie les métriques système"""
        print("\n--- Vérification Métriques Système ---")
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = "WARNING" if cpu_percent > self.thresholds['cpu_percent'] else "OK"
            self.log_metric("CPU Usage", cpu_percent, "%", cpu_status)
            
            # Mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_status = "WARNING" if memory_percent > self.thresholds['memory_percent'] else "OK"
            self.log_metric("Memory Usage", memory_percent, "%", memory_status)
            self.log_metric("Memory Available", memory.available / (1024**3), "GB")
            
            # Disque
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = "WARNING" if disk_percent > self.thresholds['disk_percent'] else "OK"
            self.log_metric("Disk Usage", disk_percent, "%", disk_status)
            self.log_metric("Disk Free", disk.free / (1024**3), "GB")
            
            # Processus Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if python_processes:
                total_cpu = sum(p['cpu_percent'] for p in python_processes)
                total_memory = sum(p['memory_percent'] for p in python_processes)
                self.log_metric("Python CPU", total_cpu, "%")
                self.log_metric("Python Memory", total_memory, "%")
            
            return True
            
        except Exception as e:
            print(f"Erreur métriques système: {e}")
            return False
    
    def check_database_health(self):
        """Vérifie la santé de la base de données"""
        print("\n--- Vérification Base de Données ---")
        
        try:
            import psycopg2
            
            # Connexion - utilise les variables d'environnement depuis .env
            # ⚠️ Aucune valeur par défaut pour la sécurité
            from decouple import config
            conn = psycopg2.connect(
                host=config('POSTGRES_HOST'),
                database=config('POSTGRES_DB'),
                user=config('POSTGRES_USER'),
                password=config('POSTGRES_PASSWORD'),
                port=config('POSTGRES_PORT')
            )
            
            with conn.cursor() as cursor:
                # Récupérer le nom de la base depuis la connexion
                db_name = config('POSTGRES_DB')
                
                # Nombre de documents
                cursor.execute("SELECT COUNT(*) FROM rag_documentembedding")
                doc_count = cursor.fetchone()[0]
                self.log_metric("Database Documents", doc_count, "docs")
                
                # Taille de la base
                cursor.execute("SELECT pg_database_size(%s)", (db_name,))
                db_size_bytes = cursor.fetchone()[0]
                db_size_mb = db_size_bytes / (1024**2)
                self.log_metric("Database Size", db_size_mb, "MB")
                
                # Connexions actives
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE datname = %s", (db_name,))
                active_connections = cursor.fetchone()[0]
                self.log_metric("Active Connections", active_connections, "conn")
                
                # Performance d'une requête test
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM rag_documentembedding WHERE created_at > NOW() - INTERVAL '1 hour'")
                recent_docs = cursor.fetchone()[0]
                query_time = (time.time() - start_time) * 1000
                
                query_status = "WARNING" if query_time > 1000 else "OK"
                self.log_metric("Query Performance", query_time, "ms", query_status)
                self.log_metric("Recent Documents", recent_docs, "docs")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erreur base de données: {e}")
            return False
    
    def check_redis_health(self):
        """Vérifie la santé de Redis"""
        print("\n--- Vérification Redis ---")
        
        try:
            import redis
            from decouple import config
            # ⚠️ Aucune valeur par défaut pour la sécurité - doit venir du .env
            client = redis.Redis(
                host=config('REDIS_HOST'),
                port=config('REDIS_PORT', cast=int),
                db=config('REDIS_DB', cast=int),
                password=config('REDIS_PASSWORD', default=None),  # Peut être vide
                decode_responses=True
            )
            
            # Ping
            ping_result = client.ping()
            self.log_metric("Redis Ping", 1 if ping_result else 0, "bool")
            
            # Informations Redis
            info = client.info()
            
            # Mémoire utilisée
            memory_used = info.get('used_memory', 0)
            memory_used_mb = memory_used / (1024**2)
            self.log_metric("Redis Memory", memory_used_mb, "MB")
            
            # Clés
            db_size = info.get('db0', {}).get('keys', 0)
            self.log_metric("Redis Keys", db_size, "keys")
            
            # Hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            self.log_metric("Redis Hit Rate", hit_rate, "%")
            
            # Connexions
            connected_clients = info.get('connected_clients', 0)
            self.log_metric("Redis Clients", connected_clients, "clients")
            
            return True
            
        except Exception as e:
            print(f"Erreur Redis: {e}")
            return False
    
    def check_api_health(self):
        """Vérifie la santé de l'API"""
        print("\n--- Vérification API ---")
        
        try:
            # Test de santé
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/health/", timeout=10)
            health_time = (time.time() - start_time) * 1000
            
            health_status = "OK" if response.status_code == 200 else "ERROR"
            self.log_metric("Health Check", health_time, "ms", health_status)
            
            # Test de recherche
            search_times = []
            success_count = 0
            
            test_questions = [
                "Quelle est la date d'inauguration de la SAR ?",
                "Quelle est la capacité de la SAR ?",
                "Quels sont les produits de la SAR ?"
            ]
            
            for question in test_questions:
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/api/mai/search/",
                    json={'question': question},
                    timeout=10
                )
                search_time = (time.time() - start_time) * 1000
                search_times.append(search_time)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        success_count += 1
            
            avg_search_time = sum(search_times) / len(search_times)
            success_rate = (success_count / len(test_questions)) * 100
            
            search_status = "WARNING" if avg_search_time > self.thresholds['response_time_ms'] else "OK"
            self.log_metric("Search Response Time", avg_search_time, "ms", search_status)
            
            success_status = "WARNING" if success_rate < self.thresholds['success_rate_percent'] else "OK"
            self.log_metric("Search Success Rate", success_rate, "%", success_status)
            
            return True
            
        except Exception as e:
            print(f"Erreur API: {e}")
            return False
    
    def check_monitoring_endpoints(self):
        """Vérifie les endpoints de monitoring"""
        print("\n--- Vérification Endpoints Monitoring ---")
        
        monitoring_endpoints = [
            ('/api/health/', 'Health Check'),
            ('/api/mai/statistics/', 'Statistics'),
            ('/api/mai/intelligent-optimization/status/', 'Optimization Status'),
            ('/api/mai/intelligent-optimization/system-health/', 'System Health'),
            ('/api/mai/intelligent-optimization/cache-stats/', 'Cache Stats'),
        ]
        
        working_endpoints = 0
        
        for endpoint, name in monitoring_endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    working_endpoints += 1
                    status = "OK"
                else:
                    status = "ERROR"
                
                self.log_metric(f"Endpoint {name}", response_time, "ms", status)
                
            except Exception as e:
                self.log_metric(f"Endpoint {name}", 0, "ms", "ERROR")
        
        endpoint_rate = (working_endpoints / len(monitoring_endpoints)) * 100
        endpoint_status = "WARNING" if endpoint_rate < 80 else "OK"
        self.log_metric("Monitoring Endpoints", endpoint_rate, "%", endpoint_status)
        
        return endpoint_rate >= 80
    
    def generate_alert(self, alert_type: str, message: str, severity: str = "WARNING"):
        """Génère une alerte"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        self.alerts.append(alert)
        
        severity_icon = "⚠️" if severity == "WARNING" else "❌"
        print(f"{severity_icon} ALERTE {severity}: {alert_type} - {message}")
        
        # Envoyer l'alerte par email si configuré
        if self.alert_config['email_enabled']:
            self.send_email_alert(alert)
    
    def send_email_alert(self, alert: Dict):
        """Envoie une alerte par email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.alert_config['email_username']
            msg['To'] = ', '.join(self.alert_config['email_recipients'])
            msg['Subject'] = f"ALERTE SAR RAG - {alert['type']}"
            
            body = f"""
            Alerte du système RAG SAR
            
            Type: {alert['type']}
            Séverité: {alert['severity']}
            Message: {alert['message']}
            Timestamp: {alert['timestamp']}
            
            Veuillez vérifier le système immédiatement.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.alert_config['email_smtp_server'], self.alert_config['email_smtp_port'])
            server.starttls()
            server.login(self.alert_config['email_username'], self.alert_config['email_password'])
            server.send_message(msg)
            server.quit()
            
            print(f"Email d'alerte envoyé: {alert['type']}")
            
        except Exception as e:
            print(f"Erreur envoi email: {e}")
    
    def analyze_metrics(self):
        """Analyse les métriques et génère des alertes"""
        print("\n--- Analyse des Métriques ---")
        
        # Analyser les métriques récentes (dernières 5 minutes)
        recent_metrics = [m for m in self.monitoring_data 
                         if datetime.fromisoformat(m['timestamp']) > datetime.now() - timedelta(minutes=5)]
        
        # Vérifier les seuils
        for metric in recent_metrics:
            if metric['status'] == "WARNING" or metric['status'] == "ERROR":
                self.generate_alert(
                    f"Metric {metric['metric']}",
                    f"Valeur: {metric['value']}{metric['unit']} (Seuil dépassé)",
                    "WARNING"
                )
        
        # Vérifier les tendances
        cpu_metrics = [m for m in recent_metrics if m['metric'] == 'CPU Usage']
        if len(cpu_metrics) > 1:
            cpu_trend = cpu_metrics[-1]['value'] - cpu_metrics[0]['value']
            if cpu_trend > 10:  # Augmentation de 10%
                self.generate_alert(
                    "CPU Trend",
                    f"Augmentation CPU de {cpu_trend:.1f}% en 5 minutes",
                    "WARNING"
                )
    
    def save_monitoring_data(self):
        """Sauvegarde les données de monitoring"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_data': self.monitoring_data,
                'alerts': self.alerts,
                'summary': {
                    'total_metrics': len(self.monitoring_data),
                    'total_alerts': len(self.alerts),
                    'warning_alerts': len([a for a in self.alerts if a['severity'] == 'WARNING']),
                    'error_alerts': len([a for a in self.alerts if a['severity'] == 'ERROR']),
                }
            }
            
            # Sauvegarder dans un fichier avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'monitoring_data_{timestamp}.json'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Données de monitoring sauvegardées: {filename}")
            
        except Exception as e:
            print(f"Erreur sauvegarde monitoring: {e}")
    
    def run_monitoring_cycle(self):
        """Exécute un cycle de monitoring complet"""
        print("MONITORING DE PRODUCTION - CYCLE COMPLET")
        print("=" * 50)
        print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Vérifications
        checks = [
            ("Métriques Système", self.check_system_metrics),
            ("Base de Données", self.check_database_health),
            ("Redis", self.check_redis_health),
            ("API", self.check_api_health),
            ("Endpoints Monitoring", self.check_monitoring_endpoints),
        ]
        
        successful_checks = 0
        
        for check_name, check_func in checks:
            print(f"\n--- {check_name} ---")
            try:
                if check_func():
                    successful_checks += 1
                    print(f"✅ {check_name} réussi")
                else:
                    print(f"❌ {check_name} échoué")
            except Exception as e:
                print(f"❌ {check_name} erreur: {e}")
        
        # Analyse des métriques
        self.analyze_metrics()
        
        # Sauvegarde des données
        self.save_monitoring_data()
        
        # Résumé
        print("\n" + "=" * 50)
        print("RÉSUMÉ DU MONITORING")
        print("=" * 50)
        print(f"Vérifications réussies: {successful_checks}/{len(checks)}")
        print(f"Total métriques: {len(self.monitoring_data)}")
        print(f"Total alertes: {len(self.alerts)}")
        
        if self.alerts:
            print("\nALERTES ACTIVES:")
            for alert in self.alerts[-5:]:  # 5 dernières alertes
                print(f"  - {alert['type']}: {alert['message']}")
        
        return successful_checks == len(checks)

def main():
    """Fonction principale"""
    monitor = ProductionMonitor()
    success = monitor.run_monitoring_cycle()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

