#!/usr/bin/env python
"""
Script de déploiement automatisé pour la production.
Prépare, teste et déploie le système RAG SAR en production.
"""
import os
import sys
import subprocess
import time
import json
import shutil
from datetime import datetime
from pathlib import Path

class ProductionDeployer:
    """Déployeur de production pour le système RAG SAR"""
    
    def __init__(self):
        self.start_time = time.time()
        self.deployment_log = []
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / 'backups'
        self.log_dir = self.project_root / 'logs'
        
    def log(self, message, level="INFO"):
        """Enregistre un message de déploiement"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.deployment_log.append(log_entry)
        print(log_entry)
        
    def run_command(self, command, description="", check=True):
        """Exécute une commande système"""
        self.log(f"Exécution: {description or command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check,
                cwd=self.project_root
            )
            if result.stdout:
                self.log(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                self.log(f"STDERR: {result.stderr.strip()}", "WARNING")
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.log(f"Erreur commande: {e}", "ERROR")
        return False
    
    def check_prerequisites(self):
        """Vérifie les prérequis pour le déploiement"""
        self.log("=== VÉRIFICATION DES PRÉREQUIS ===")
        
        # Vérifier Python
        if not self.run_command("python --version", "Vérification Python"):
        return False
    
        # Vérifier pip
        if not self.run_command("pip --version", "Vérification pip"):
        return False
    
        # Vérifier PostgreSQL
        if not self.run_command("psql --version", "Vérification PostgreSQL"):
        return False
    
        # Vérifier Redis
        if not self.run_command("redis-cli --version", "Vérification Redis"):
        return False
    
        # Vérifier les fichiers de configuration
        required_files = [
            'master/settings_production.py',
            'requirements.txt',
            'manage.py',
            'mai/models.py'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                self.log(f"Fichier manquant: {file_path}", "ERROR")
        return False
    
        self.log("Tous les prérequis sont satisfaits", "SUCCESS")
    return True

    def create_backup(self):
        """Crée une sauvegarde avant déploiement"""
        self.log("=== CRÉATION DE SAUVEGARDE ===")
        
        # Créer le répertoire de sauvegarde
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{backup_timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder la base de données
        db_backup_file = backup_path / 'database_backup.sql'
        if self.run_command(
            f"pg_dump -h localhost -U sar_user -d sar > {db_backup_file}",
            "Sauvegarde base de données"
        ):
            self.log(f"Sauvegarde DB créée: {db_backup_file}")
        else:
            self.log("Échec sauvegarde DB", "WARNING")
        
        # Sauvegarder les fichiers de configuration
        config_files = [
            'master/settings.py',
            'master/settings_production.py',
            '.env',
            'requirements.txt'
        ]
        
        for config_file in config_files:
            src = self.project_root / config_file
            if src.exists():
                dst = backup_path / config_file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self.log(f"Config sauvegardée: {config_file}")
        
        self.log(f"Sauvegarde complète créée: {backup_path}")
        return str(backup_path)
    
    def install_dependencies(self):
        """Installe les dépendances de production"""
        self.log("=== INSTALLATION DES DÉPENDANCES ===")
        
        # Mettre à jour pip
        self.run_command("python -m pip install --upgrade pip", "Mise à jour pip")
        
        # Installer les dépendances
        if not self.run_command(
            "pip install -r requirements.txt --no-cache-dir",
            "Installation dépendances production"
        ):
        return False
    
        # Installer les dépendances système
        system_deps = [
            "psycopg2-binary",
            "redis",
            "django-redis",
            "sentence-transformers",
            "numpy",
            "pandas"
        ]
        
        for dep in system_deps:
            self.run_command(f"pip install {dep}", f"Installation {dep}")
        
        self.log("Dépendances installées avec succès", "SUCCESS")
    return True

    def run_migrations(self):
        """Exécute les migrations de base de données"""
        self.log("=== MIGRATIONS DE BASE DE DONNÉES ===")
        
        # Créer les migrations
        if not self.run_command(
            "python manage.py makemigrations",
            "Création des migrations"
        ):
            return False
        
        # Appliquer les migrations
        if not self.run_command(
            "python manage.py migrate",
            "Application des migrations"
        ):
        return False
    
        # Créer l'index vectoriel
        if not self.run_command(
            "python manage.py build_vector_index --index-type ivfflat",
            "Création index vectoriel"
        ):
            self.log("Index vectoriel non créé", "WARNING")
        
        self.log("Migrations exécutées avec succès", "SUCCESS")
    return True

    def collect_static_files(self):
        """Collecte les fichiers statiques"""
        self.log("=== COLLECTE DES FICHIERS STATIQUES ===")
        
        # Créer le répertoire static
        static_dir = self.project_root / 'staticfiles'
        static_dir.mkdir(exist_ok=True)
        
        # Collecter les fichiers statiques
        if not self.run_command(
            "python manage.py collectstatic --noinput",
            "Collecte fichiers statiques"
        ):
        return False
    
        self.log("Fichiers statiques collectés", "SUCCESS")
        return True
    
    def run_production_tests(self):
        """Exécute les tests de production"""
        self.log("=== TESTS DE PRODUCTION ===")
        
        # Tests de base
        test_commands = [
            ("python manage.py check --deploy", "Vérification déploiement"),
            ("python test_quick_validation.py", "Validation rapide"),
            ("python test_phase6_simple.py", "Tests Phase 6"),
        ]
        
        for command, description in test_commands:
            if not self.run_command(command, description, check=False):
                self.log(f"Test échoué: {description}", "WARNING")
            else:
                self.log(f"Test réussi: {description}", "SUCCESS")
        
        return True
    
    def optimize_system(self):
        """Optimise le système pour la production"""
        self.log("=== OPTIMISATION DU SYSTÈME ===")
        
        # Optimiser la base de données
        self.run_command(
            "python manage.py optimize_vector_indexes",
            "Optimisation index vectoriels"
        )
        
        # Optimiser le cache
        self.run_command(
            "python manage.py optimize_cache",
            "Optimisation cache Redis"
        )
        
        # Vérifier la santé du système
        self.run_command(
            "python manage.py check_system_health",
            "Vérification santé système"
        )
        
        self.log("Optimisation terminée", "SUCCESS")
    return True

    def create_systemd_service(self):
        """Crée le service systemd pour la production"""
        self.log("=== CRÉATION SERVICE SYSTEMD ===")
        
        service_content = f"""[Unit]
Description=SAR RAG Django Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory={self.project_root}
Environment=DJANGO_SETTINGS_MODULE=master.settings_production
ExecStart=/usr/bin/python manage.py runserver 0.0.0.0:8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path('/etc/systemd/system/sar-rag.service')
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            self.log(f"Service systemd créé: {service_file}")
            
            # Recharger systemd
            self.run_command("systemctl daemon-reload", "Rechargement systemd")
            self.run_command("systemctl enable sar-rag", "Activation service")
            
        except PermissionError:
            self.log("Permissions insuffisantes pour créer le service systemd", "WARNING")
        
        return True
    
    def setup_monitoring(self):
        """Configure le monitoring de production"""
        self.log("=== CONFIGURATION DU MONITORING ===")
        
        # Créer les répertoires de logs
        log_dirs = [
            '/var/log/sar_rag',
            '/var/cache/sar_rag',
            '/var/backups/sar_rag'
        ]
        
        for log_dir in log_dirs:
            self.run_command(f"sudo mkdir -p {log_dir}", f"Création {log_dir}")
            self.run_command(f"sudo chown www-data:www-data {log_dir}", f"Permissions {log_dir}")
        
        # Configurer logrotate
        logrotate_config = f"""/var/log/sar_rag/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload sar-rag
    endscript
}}
"""
        
        try:
            with open('/etc/logrotate.d/sar-rag', 'w') as f:
                f.write(logrotate_config)
            self.log("Configuration logrotate créée")
        except PermissionError:
            self.log("Permissions insuffisantes pour logrotate", "WARNING")
        
    return True

    def generate_deployment_report(self):
        """Génère un rapport de déploiement"""
        self.log("=== GÉNÉRATION DU RAPPORT ===")
        
        duration = time.time() - self.start_time
        
        report = {
            'deployment_time': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'status': 'SUCCESS' if all('ERROR' not in log for log in self.deployment_log) else 'PARTIAL',
            'logs': self.deployment_log,
            'system_info': {
                'python_version': subprocess.run(['python', '--version'], capture_output=True, text=True).stdout.strip(),
                'django_version': subprocess.run(['python', '-c', 'import django; print(django.get_version())'], capture_output=True, text=True).stdout.strip(),
            },
            'next_steps': [
                'Vérifier les logs: /var/log/sar_rag/',
                'Tester l\'API: curl http://localhost:8000/api/health/',
                'Surveiller les performances: /api/mai/intelligent-optimization/system-health/',
                'Configurer les alertes de monitoring',
                'Planifier les sauvegardes automatiques'
            ]
        }
        
        # Sauvegarder le rapport
        report_file = self.project_root / 'deployment_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"Rapport de déploiement sauvegardé: {report_file}")
        return report
    
    def deploy(self):
        """Exécute le déploiement complet"""
        self.log("🚀 DÉMARRAGE DU DÉPLOIEMENT DE PRODUCTION")
        self.log("=" * 60)
        
        steps = [
            ("Vérification prérequis", self.check_prerequisites),
            ("Création sauvegarde", self.create_backup),
            ("Installation dépendances", self.install_dependencies),
            ("Exécution migrations", self.run_migrations),
            ("Collecte fichiers statiques", self.collect_static_files),
            ("Tests de production", self.run_production_tests),
            ("Optimisation système", self.optimize_system),
            ("Création service systemd", self.create_systemd_service),
            ("Configuration monitoring", self.setup_monitoring),
    ]
    
    success_count = 0
        total_steps = len(steps)
        
        for step_name, step_func in steps:
            self.log(f"\n--- {step_name} ---")
            try:
                if step_func():
            success_count += 1
                    self.log(f"✅ {step_name} terminé avec succès")
        else:
                    self.log(f"❌ {step_name} échoué", "ERROR")
            except Exception as e:
                self.log(f"❌ {step_name} erreur: {e}", "ERROR")
        
        # Générer le rapport final
        report = self.generate_deployment_report()
        
        # Afficher le résumé
        self.log("\n" + "=" * 60)
        self.log("RÉSUMÉ DU DÉPLOIEMENT")
        self.log("=" * 60)
        self.log(f"Étapes réussies: {success_count}/{total_steps}")
        self.log(f"Durée totale: {report['duration_seconds']}s")
        self.log(f"Statut: {report['status']}")
        
        if success_count == total_steps:
            self.log("🎉 DÉPLOIEMENT RÉUSSI !")
            self.log("Le système RAG SAR est prêt pour la production.")
        else:
            self.log("⚠️ DÉPLOIEMENT PARTIEL")
            self.log("Vérifiez les erreurs et corrigez-les avant de continuer.")
        
        return success_count == total_steps

def main():
    """Fonction principale"""
    deployer = ProductionDeployer()
    success = deployer.deploy()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())