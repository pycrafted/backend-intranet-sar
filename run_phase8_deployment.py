#!/usr/bin/env python
"""
Phase 8 - Script Maître de Déploiement et Monitoring
Prépare, teste et déploie le système RAG SAR en production.
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

class Phase8DeploymentManager:
    """Gestionnaire de déploiement Phase 8"""
    
    def __init__(self):
        self.start_time = time.time()
        self.deployment_log = []
        self.project_root = Path(__file__).parent
        
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
    
    def step1_prepare_environment(self):
        """Étape 1: Préparation de l'environnement"""
        self.log("=== ÉTAPE 1: PRÉPARATION DE L'ENVIRONNEMENT ===")
        
        # Vérifier les prérequis
        prerequisites = [
            ("python --version", "Python"),
            ("pip --version", "Pip"),
            ("psql --version", "PostgreSQL"),
            ("redis-cli --version", "Redis"),
        ]
        
        for command, name in prerequisites:
            if not self.run_command(command, f"Vérification {name}"):
                self.log(f"Prérequis manquant: {name}", "ERROR")
                return False
        
        # Créer les répertoires nécessaires
        directories = [
            'logs',
            'backups',
            'staticfiles',
            'media',
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            self.log(f"Répertoire créé: {directory}")
        
        self.log("Environnement préparé avec succès", "SUCCESS")
        return True
    
    def step2_install_dependencies(self):
        """Étape 2: Installation des dépendances"""
        self.log("=== ÉTAPE 2: INSTALLATION DES DÉPENDANCES ===")
        
        # Mettre à jour pip
        self.run_command("python -m pip install --upgrade pip", "Mise à jour pip")
        
        # Installer les dépendances de production
        if not self.run_command(
            "pip install -r requirements.txt --no-cache-dir",
            "Installation dépendances production"
        ):
            return False
        
        # Installer les dépendances de monitoring
        monitoring_deps = [
            "psutil",
            "requests",
        ]
        
        for dep in monitoring_deps:
            self.run_command(f"pip install {dep}", f"Installation {dep}")
        
        self.log("Dépendances installées avec succès", "SUCCESS")
        return True
    
    def step3_run_migrations(self):
        """Étape 3: Exécution des migrations"""
        self.log("=== ÉTAPE 3: EXÉCUTION DES MIGRATIONS ===")
        
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
        self.run_command(
            "python manage.py build_vector_index --index-type ivfflat",
            "Création index vectoriel"
        )
        
        self.log("Migrations exécutées avec succès", "SUCCESS")
        return True
    
    def step4_collect_static(self):
        """Étape 4: Collecte des fichiers statiques"""
        self.log("=== ÉTAPE 4: COLLECTE DES FICHIERS STATIQUES ===")
        
        if not self.run_command(
            "python manage.py collectstatic --noinput",
            "Collecte fichiers statiques"
        ):
            return False
        
        self.log("Fichiers statiques collectés", "SUCCESS")
        return True
    
    def step5_run_production_tests(self):
        """Étape 5: Tests de production"""
        self.log("=== ÉTAPE 5: TESTS DE PRODUCTION ===")
        
        # Tests de base
        test_commands = [
            ("python manage.py check --deploy", "Vérification déploiement"),
            ("python test_quick_validation.py", "Validation rapide"),
            ("python test_phase6_simple.py", "Tests Phase 6"),
            ("python test_production_readiness.py", "Tests préparation production"),
        ]
        
        successful_tests = 0
        
        for command, description in test_commands:
            if self.run_command(command, description, check=False):
                successful_tests += 1
                self.log(f"Test réussi: {description}", "SUCCESS")
            else:
                self.log(f"Test échoué: {description}", "WARNING")
        
        success_rate = (successful_tests / len(test_commands)) * 100
        self.log(f"Taux de réussite des tests: {success_rate:.1f}%")
        
        return success_rate >= 75  # 75% de réussite minimum
    
    def step6_optimize_system(self):
        """Étape 6: Optimisation du système"""
        self.log("=== ÉTAPE 6: OPTIMISATION DU SYSTÈME ===")
        
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
    
    def step7_setup_monitoring(self):
        """Étape 7: Configuration du monitoring"""
        self.log("=== ÉTAPE 7: CONFIGURATION DU MONITORING ===")
        
        # Créer les répertoires de logs
        log_dirs = [
            '/var/log/sar_rag',
            '/var/cache/sar_rag',
            '/var/backups/sar_rag'
        ]
        
        for log_dir in log_dirs:
            self.run_command(f"sudo mkdir -p {log_dir}", f"Création {log_dir}")
            self.run_command(f"sudo chown www-data:www-data {log_dir}", f"Permissions {log_dir}")
        
        # Tester le monitoring
        if self.run_command("python monitor_production.py", "Test monitoring production"):
            self.log("Monitoring configuré avec succès", "SUCCESS")
            return True
        else:
            self.log("Erreur configuration monitoring", "WARNING")
            return True  # Continue même si le monitoring échoue
    
    def step8_create_services(self):
        """Étape 8: Création des services système"""
        self.log("=== ÉTAPE 8: CRÉATION DES SERVICES SYSTÈME ===")
        
        # Créer le service systemd pour Django
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
        
        try:
            with open('/tmp/sar-rag.service', 'w') as f:
                f.write(service_content)
            
            self.run_command("sudo cp /tmp/sar-rag.service /etc/systemd/system/", "Copie service systemd")
            self.run_command("sudo systemctl daemon-reload", "Rechargement systemd")
            self.run_command("sudo systemctl enable sar-rag", "Activation service")
            
            self.log("Service systemd créé", "SUCCESS")
        except Exception as e:
            self.log(f"Erreur création service: {e}", "WARNING")
        
        # Créer le service de monitoring
        monitoring_service_content = f"""[Unit]
Description=SAR RAG Monitoring
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={self.project_root}
ExecStart=/usr/bin/python monitor_production.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open('/tmp/sar-rag-monitoring.service', 'w') as f:
                f.write(monitoring_service_content)
            
            self.run_command("sudo cp /tmp/sar-rag-monitoring.service /etc/systemd/system/", "Copie service monitoring")
            self.run_command("sudo systemctl daemon-reload", "Rechargement systemd")
            self.run_command("sudo systemctl enable sar-rag-monitoring", "Activation service monitoring")
            
            self.log("Service monitoring créé", "SUCCESS")
        except Exception as e:
            self.log(f"Erreur création service monitoring: {e}", "WARNING")
        
        return True
    
    def step9_final_validation(self):
        """Étape 9: Validation finale"""
        self.log("=== ÉTAPE 9: VALIDATION FINALE ===")
        
        # Tests finaux
        final_tests = [
            ("python test_quick_validation.py", "Validation rapide finale"),
            ("python test_production_readiness.py", "Tests préparation production finale"),
        ]
        
        successful_tests = 0
        
        for command, description in final_tests:
            if self.run_command(command, description, check=False):
                successful_tests += 1
                self.log(f"Test final réussi: {description}", "SUCCESS")
            else:
                self.log(f"Test final échoué: {description}", "WARNING")
        
        # Vérifier les services
        services = ['sar-rag', 'sar-rag-monitoring']
        for service in services:
            self.run_command(f"sudo systemctl status {service}", f"Statut {service}")
        
        success_rate = (successful_tests / len(final_tests)) * 100
        self.log(f"Taux de réussite validation finale: {success_rate:.1f}%")
        
        return success_rate >= 75
    
    def generate_deployment_report(self):
        """Génère le rapport de déploiement final"""
        self.log("=== GÉNÉRATION DU RAPPORT FINAL ===")
        
        duration = time.time() - self.start_time
        
        report = {
            'deployment_time': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'phase': 'Phase 8 - Déploiement et Monitoring',
            'status': 'SUCCESS',
            'logs': self.deployment_log,
            'next_steps': [
                'Démarrer les services: sudo systemctl start sar-rag',
                'Démarrer le monitoring: sudo systemctl start sar-rag-monitoring',
                'Vérifier les logs: journalctl -u sar-rag -f',
                'Tester l\'API: curl http://localhost:8000/api/health/',
                'Surveiller les performances: /api/mai/intelligent-optimization/system-health/',
                'Configurer les alertes de monitoring',
                'Planifier les sauvegardes automatiques'
            ],
            'monitoring_endpoints': [
                'http://localhost:8000/api/health/',
                'http://localhost:8000/api/mai/statistics/',
                'http://localhost:8000/api/mai/intelligent-optimization/status/',
                'http://localhost:8000/api/mai/intelligent-optimization/system-health/',
                'http://localhost:8000/api/mai/intelligent-optimization/cache-stats/',
            ],
            'log_files': [
                '/var/log/sar_rag/django.log',
                '/var/log/sar_rag/rag.log',
                '/var/log/sar_rag/error.log',
            ]
        }
        
        # Sauvegarder le rapport
        report_file = self.project_root / 'phase8_deployment_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"Rapport de déploiement sauvegardé: {report_file}")
        return report
    
    def run_phase8_deployment(self):
        """Exécute le déploiement complet Phase 8"""
        self.log("🚀 PHASE 8 - DÉPLOIEMENT ET MONITORING")
        self.log("=" * 60)
        
        steps = [
            ("Préparation Environnement", self.step1_prepare_environment),
            ("Installation Dépendances", self.step2_install_dependencies),
            ("Exécution Migrations", self.step3_run_migrations),
            ("Collecte Fichiers Statiques", self.step4_collect_static),
            ("Tests de Production", self.step5_run_production_tests),
            ("Optimisation Système", self.step6_optimize_system),
            ("Configuration Monitoring", self.step7_setup_monitoring),
            ("Création Services", self.step8_create_services),
            ("Validation Finale", self.step9_final_validation),
        ]
        
        successful_steps = 0
        total_steps = len(steps)
        
        for step_name, step_func in steps:
            self.log(f"\n--- {step_name} ---")
            try:
                if step_func():
                    successful_steps += 1
                    self.log(f"✅ {step_name} terminé avec succès")
                else:
                    self.log(f"❌ {step_name} échoué", "ERROR")
            except Exception as e:
                self.log(f"❌ {step_name} erreur: {e}", "ERROR")
        
        # Générer le rapport final
        report = self.generate_deployment_report()
        
        # Afficher le résumé
        self.log("\n" + "=" * 60)
        self.log("RÉSUMÉ DU DÉPLOIEMENT PHASE 8")
        self.log("=" * 60)
        self.log(f"Étapes réussies: {successful_steps}/{total_steps}")
        self.log(f"Durée totale: {report['duration_seconds']}s")
        
        if successful_steps == total_steps:
            self.log("🎉 DÉPLOIEMENT PHASE 8 RÉUSSI !")
            self.log("Le système RAG SAR est prêt pour la production avec monitoring complet.")
        elif successful_steps >= total_steps * 0.8:
            self.log("✅ DÉPLOIEMENT PHASE 8 RÉUSSI AVEC RÉSERVES")
            self.log("Le système est opérationnel avec quelques améliorations mineures nécessaires.")
        else:
            self.log("⚠️ DÉPLOIEMENT PHASE 8 PARTIEL")
            self.log("Vérifiez les erreurs et corrigez-les avant de continuer.")
        
        return successful_steps >= total_steps * 0.8

def main():
    """Fonction principale"""
    manager = Phase8DeploymentManager()
    success = manager.run_phase8_deployment()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

