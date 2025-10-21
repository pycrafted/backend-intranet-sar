"""
Système de maintenance prédictive pour la Phase 5.
Prédit les problèmes et planifie la maintenance automatiquement.
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db import models
from mai.models import RAGSearchLog, DocumentEmbedding
from mai.vector_search_service import vector_search_service
from mai.embedding_service import embedding_service
from mai.services import MAIService

logger = logging.getLogger(__name__)

class PredictiveMaintenance:
    """Système de maintenance prédictive intelligent"""
    
    def __init__(self):
        self.maintenance_config = self._load_maintenance_config()
        self.prediction_history = []
        self.maintenance_schedule = []
        
    def _load_maintenance_config(self) -> Dict[str, Any]:
        """Charge la configuration de maintenance"""
        return {
            'prediction': {
                'lookback_days': 30,
                'prediction_horizon_days': 7,
                'confidence_threshold': 0.8,
                'anomaly_threshold': 2.0
            },
            'maintenance': {
                'preventive_interval_days': 7,
                'corrective_threshold': 0.9,
                'auto_schedule_enabled': True,
                'maintenance_window_hours': 2
            },
            'alerts': {
                'performance_degradation': 0.2,
                'error_rate_increase': 0.1,
                'resource_usage_critical': 0.9,
                'data_quality_decline': 0.15
            }
        }
    
    def run_predictive_analysis(self) -> Dict[str, Any]:
        """Exécute une analyse prédictive complète"""
        start_time = time.time()
        analysis_results = {
            'timestamp': timezone.now().isoformat(),
            'duration_seconds': 0,
            'predictions': [],
            'anomalies': [],
            'maintenance_recommendations': [],
            'risk_assessment': {},
            'confidence_scores': {}
        }
        
        try:
            logger.info("Démarrage de l'analyse prédictive")
            
            # 1. Analyse des tendances
            trends = self._analyze_trends()
            analysis_results['trends'] = trends
            
            # 2. Détection d'anomalies
            anomalies = self._detect_anomalies()
            analysis_results['anomalies'] = anomalies
            
            # 3. Prédictions de performance
            performance_predictions = self._predict_performance()
            analysis_results['predictions'].extend(performance_predictions)
            
            # 4. Prédictions de ressources
            resource_predictions = self._predict_resource_usage()
            analysis_results['predictions'].extend(resource_predictions)
            
            # 5. Prédictions de qualité
            quality_predictions = self._predict_data_quality()
            analysis_results['predictions'].extend(quality_predictions)
            
            # 6. Évaluation des risques
            risk_assessment = self._assess_risks(analysis_results)
            analysis_results['risk_assessment'] = risk_assessment
            
            # 7. Recommandations de maintenance
            maintenance_recommendations = self._generate_maintenance_recommendations(analysis_results)
            analysis_results['maintenance_recommendations'] = maintenance_recommendations
            
            # 8. Planification automatique
            if self.maintenance_config['maintenance']['auto_schedule_enabled']:
                scheduled_maintenance = self._schedule_maintenance(analysis_results)
                analysis_results['scheduled_maintenance'] = scheduled_maintenance
            
            # Calculer la durée
            analysis_results['duration_seconds'] = time.time() - start_time
            
            # Logger les résultats
            self._log_prediction_results(analysis_results)
            
            logger.info(f"Analyse prédictive terminée en {analysis_results['duration_seconds']:.2f}s")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse prédictive: {e}")
            analysis_results['error'] = str(e)
            return analysis_results
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyse les tendances du système"""
        try:
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=self.maintenance_config['prediction']['lookback_days'])
            
            # Récupérer les données
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            ).order_by('created_at')
            
            # Analyser les tendances par jour
            daily_trends = self._analyze_daily_trends(logs, start_time, end_time)
            
            # Analyser les tendances par heure
            hourly_trends = self._analyze_hourly_trends(logs, start_time, end_time)
            
            # Analyser les tendances de performance
            performance_trends = self._analyze_performance_trends(logs)
            
            # Analyser les tendances d'utilisation
            usage_trends = self._analyze_usage_trends(logs)
            
            return {
                'daily_trends': daily_trends,
                'hourly_trends': hourly_trends,
                'performance_trends': performance_trends,
                'usage_trends': usage_trends,
                'trend_direction': self._calculate_trend_direction(daily_trends, performance_trends)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances: {e}")
            return {'error': str(e)}
    
    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """Détecte les anomalies dans le système"""
        try:
            anomalies = []
            
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=7)  # Dernière semaine
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            # Anomalie 1: Pic de temps de réponse
            response_time_anomalies = self._detect_response_time_anomalies(logs)
            anomalies.extend(response_time_anomalies)
            
            # Anomalie 2: Pic de taux d'erreur
            error_rate_anomalies = self._detect_error_rate_anomalies(logs)
            anomalies.extend(error_rate_anomalies)
            
            # Anomalie 3: Pic d'utilisation des ressources
            resource_anomalies = self._detect_resource_anomalies()
            anomalies.extend(resource_anomalies)
            
            # Anomalie 4: Dégradation de la qualité des données
            data_quality_anomalies = self._detect_data_quality_anomalies()
            anomalies.extend(data_quality_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies: {e}")
            return []
    
    def _predict_performance(self) -> List[Dict[str, Any]]:
        """Prédit les performances futures"""
        try:
            predictions = []
            
            # Prédiction 1: Temps de réponse
            response_time_prediction = self._predict_response_time()
            if response_time_prediction:
                predictions.append(response_time_prediction)
            
            # Prédiction 2: Taux de succès
            success_rate_prediction = self._predict_success_rate()
            if success_rate_prediction:
                predictions.append(success_rate_prediction)
            
            # Prédiction 3: Charge de travail
            workload_prediction = self._predict_workload()
            if workload_prediction:
                predictions.append(workload_prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur prédiction performance: {e}")
            return []
    
    def _predict_resource_usage(self) -> List[Dict[str, Any]]:
        """Prédit l'utilisation des ressources"""
        try:
            predictions = []
            
            # Prédiction 1: Utilisation mémoire
            memory_prediction = self._predict_memory_usage()
            if memory_prediction:
                predictions.append(memory_prediction)
            
            # Prédiction 2: Utilisation CPU
            cpu_prediction = self._predict_cpu_usage()
            if cpu_prediction:
                predictions.append(cpu_prediction)
            
            # Prédiction 3: Utilisation disque
            disk_prediction = self._predict_disk_usage()
            if disk_prediction:
                predictions.append(disk_prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur prédiction ressources: {e}")
            return []
    
    def _predict_data_quality(self) -> List[Dict[str, Any]]:
        """Prédit la qualité des données"""
        try:
            predictions = []
            
            # Prédiction 1: Qualité des embeddings
            embedding_quality_prediction = self._predict_embedding_quality()
            if embedding_quality_prediction:
                predictions.append(embedding_quality_prediction)
            
            # Prédiction 2: Dégradation des métadonnées
            metadata_quality_prediction = self._predict_metadata_quality()
            if metadata_quality_prediction:
                predictions.append(metadata_quality_prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur prédiction qualité données: {e}")
            return []
    
    def _assess_risks(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue les risques du système"""
        try:
            risks = {
                'high_risk': [],
                'medium_risk': [],
                'low_risk': [],
                'overall_risk_score': 0.0
            }
            
            # Analyser les anomalies
            anomalies = analysis_results.get('anomalies', [])
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'low')
                if severity == 'high':
                    risks['high_risk'].append(anomaly)
                elif severity == 'medium':
                    risks['medium_risk'].append(anomaly)
                else:
                    risks['low_risk'].append(anomaly)
            
            # Analyser les prédictions
            predictions = analysis_results.get('predictions', [])
            for prediction in predictions:
                confidence = prediction.get('confidence', 0.0)
                impact = prediction.get('impact', 'low')
                
                if confidence > 0.8 and impact == 'high':
                    risks['high_risk'].append(prediction)
                elif confidence > 0.6 and impact in ['high', 'medium']:
                    risks['medium_risk'].append(prediction)
                else:
                    risks['low_risk'].append(prediction)
            
            # Calculer le score de risque global
            high_risk_count = len(risks['high_risk'])
            medium_risk_count = len(risks['medium_risk'])
            low_risk_count = len(risks['low_risk'])
            
            total_risks = high_risk_count + medium_risk_count + low_risk_count
            if total_risks > 0:
                risks['overall_risk_score'] = (high_risk_count * 1.0 + medium_risk_count * 0.5 + low_risk_count * 0.1) / total_risks
            
            return risks
            
        except Exception as e:
            logger.error(f"Erreur évaluation risques: {e}")
            return {'error': str(e)}
    
    def _generate_maintenance_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des recommandations de maintenance"""
        try:
            recommendations = []
            
            # Recommandations basées sur les anomalies
            anomalies = analysis_results.get('anomalies', [])
            for anomaly in anomalies:
                if anomaly.get('severity') == 'high':
                    recommendations.append({
                        'type': 'corrective',
                        'priority': 'high',
                        'title': f'Maintenance corrective: {anomaly.get("type", "Anomalie")}',
                        'description': anomaly.get('description', ''),
                        'scheduled_time': self._calculate_maintenance_window(),
                        'estimated_duration': '30 minutes',
                        'actions': self._get_corrective_actions(anomaly)
                    })
            
            # Recommandations basées sur les prédictions
            predictions = analysis_results.get('predictions', [])
            for prediction in predictions:
                if prediction.get('confidence', 0) > 0.8 and prediction.get('impact') == 'high':
                    recommendations.append({
                        'type': 'preventive',
                        'priority': 'medium',
                        'title': f'Maintenance préventive: {prediction.get("type", "Prédiction")}',
                        'description': prediction.get('description', ''),
                        'scheduled_time': self._calculate_preventive_window(),
                        'estimated_duration': '1 heure',
                        'actions': self._get_preventive_actions(prediction)
                    })
            
            # Recommandations basées sur les risques
            risk_assessment = analysis_results.get('risk_assessment', {})
            if risk_assessment.get('overall_risk_score', 0) > 0.7:
                recommendations.append({
                    'type': 'emergency',
                    'priority': 'critical',
                    'title': 'Maintenance d\'urgence requise',
                    'description': 'Score de risque élevé détecté',
                    'scheduled_time': timezone.now().isoformat(),
                    'estimated_duration': '2 heures',
                    'actions': [
                        'Vérification complète du système',
                        'Redémarrage des services critiques',
                        'Optimisation des paramètres',
                        'Surveillance renforcée'
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return []
    
    def _schedule_maintenance(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Planifie automatiquement la maintenance"""
        try:
            scheduled_maintenance = []
            
            # Planifier la maintenance préventive
            preventive_maintenance = {
                'type': 'preventive',
                'scheduled_time': self._calculate_preventive_window(),
                'duration_hours': 2,
                'description': 'Maintenance préventive programmée',
                'actions': [
                    'Nettoyage des logs',
                    'Optimisation de la base de données',
                    'Vérification des performances',
                    'Mise à jour des index'
                ],
                'auto_execute': True
            }
            scheduled_maintenance.append(preventive_maintenance)
            
            # Planifier la maintenance corrective si nécessaire
            anomalies = analysis_results.get('anomalies', [])
            high_severity_anomalies = [a for a in anomalies if a.get('severity') == 'high']
            
            if high_severity_anomalies:
                corrective_maintenance = {
                    'type': 'corrective',
                    'scheduled_time': self._calculate_corrective_window(),
                    'duration_hours': 1,
                    'description': 'Maintenance corrective pour anomalies critiques',
                    'actions': [
                        'Diagnostic des anomalies',
                        'Correction des problèmes identifiés',
                        'Test de fonctionnement',
                        'Validation des performances'
                    ],
                    'auto_execute': False  # Requiert intervention manuelle
                }
                scheduled_maintenance.append(corrective_maintenance)
            
            return scheduled_maintenance
            
        except Exception as e:
            logger.error(f"Erreur planification maintenance: {e}")
            return []
    
    # Méthodes d'analyse spécifiques
    def _analyze_daily_trends(self, logs, start_time, end_time) -> Dict[str, Any]:
        """Analyse les tendances quotidiennes"""
        try:
            daily_stats = {}
            current_date = start_time.date()
            end_date = end_time.date()
            
            while current_date <= end_date:
                day_logs = logs.filter(created_at__date=current_date)
                
                if day_logs.exists():
                    daily_stats[str(current_date)] = {
                        'total_searches': day_logs.count(),
                        'success_rate': day_logs.filter(success=True).count() / day_logs.count(),
                        'avg_response_time': day_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0
                    }
                
                current_date += timedelta(days=1)
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances quotidiennes: {e}")
            return {}
    
    def _analyze_hourly_trends(self, logs, start_time, end_time) -> Dict[str, Any]:
        """Analyse les tendances horaires"""
        try:
            hourly_stats = {}
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_hour <= end_time:
                next_hour = current_hour + timedelta(hours=1)
                hour_logs = logs.filter(created_at__range=(current_hour, next_hour))
                
                if hour_logs.exists():
                    hourly_stats[current_hour.strftime('%H:00')] = {
                        'total_searches': hour_logs.count(),
                        'success_rate': hour_logs.filter(success=True).count() / hour_logs.count(),
                        'avg_response_time': hour_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0
                    }
                
                current_hour = next_hour
            
            return hourly_stats
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances horaires: {e}")
            return {}
    
    def _detect_response_time_anomalies(self, logs) -> List[Dict[str, Any]]:
        """Détecte les anomalies de temps de réponse"""
        try:
            anomalies = []
            
            # Calculer la moyenne et l'écart-type
            response_times = list(logs.values_list('response_time_ms', flat=True))
            if len(response_times) > 10:
                avg_time = sum(response_times) / len(response_times)
                variance = sum((x - avg_time) ** 2 for x in response_times) / len(response_times)
                std_dev = variance ** 0.5
                
                # Détecter les valeurs aberrantes
                threshold = avg_time + 2 * std_dev
                outliers = [t for t in response_times if t > threshold]
                
                if outliers:
                    anomalies.append({
                        'type': 'response_time_anomaly',
                        'severity': 'high' if len(outliers) > len(response_times) * 0.1 else 'medium',
                        'description': f'Pic de temps de réponse détecté: {max(outliers):.1f}ms',
                        'affected_queries': len(outliers),
                        'threshold': threshold,
                        'max_time': max(outliers)
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies temps de réponse: {e}")
            return []
    
    def _detect_error_rate_anomalies(self, logs) -> List[Dict[str, Any]]:
        """Détecte les anomalies de taux d'erreur"""
        try:
            anomalies = []
            
            # Calculer le taux d'erreur global
            total_logs = logs.count()
            error_logs = logs.filter(success=False).count()
            error_rate = error_logs / total_logs if total_logs > 0 else 0
            
            # Seuil d'alerte
            error_threshold = self.maintenance_config['alerts']['error_rate_increase']
            
            if error_rate > error_threshold:
                anomalies.append({
                    'type': 'error_rate_anomaly',
                    'severity': 'high' if error_rate > 0.2 else 'medium',
                    'description': f'Taux d\'erreur élevé détecté: {error_rate:.1%}',
                    'error_rate': error_rate,
                    'threshold': error_threshold,
                    'total_errors': error_logs
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies taux d'erreur: {e}")
            return []
    
    def _predict_response_time(self) -> Optional[Dict[str, Any]]:
        """Prédit le temps de réponse futur"""
        try:
            # Analyse simplifiée des tendances
            # (Dans un vrai système, on utiliserait des modèles ML)
            
            # Récupérer les données des 7 derniers jours
            end_time = timezone.now()
            start_time = end_time - timedelta(days=7)
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            response_times = list(logs.values_list('response_time_ms', flat=True))
            if len(response_times) > 10:
                avg_time = sum(response_times) / len(response_times)
                
                # Prédiction simple basée sur la tendance
                # (Dans un vrai système, on utiliserait une régression)
                predicted_time = avg_time * 1.1  # +10% de croissance
                
                return {
                    'type': 'response_time_prediction',
                    'current_avg_ms': avg_time,
                    'predicted_avg_ms': predicted_time,
                    'confidence': 0.7,
                    'impact': 'medium' if predicted_time > 1000 else 'low',
                    'description': f'Temps de réponse prédit: {predicted_time:.1f}ms',
                    'trend': 'increasing' if predicted_time > avg_time else 'stable'
                }
            
        except Exception as e:
            logger.error(f"Erreur prédiction temps de réponse: {e}")
            return None
    
    def _calculate_maintenance_window(self) -> str:
        """Calcule une fenêtre de maintenance optimale"""
        # Fenêtre de maintenance: 2h-4h du matin
        now = timezone.now()
        maintenance_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
        
        # Si c'est déjà passé aujourd'hui, programmer pour demain
        if maintenance_time <= now:
            maintenance_time += timedelta(days=1)
        
        return maintenance_time.isoformat()
    
    def _calculate_preventive_window(self) -> str:
        """Calcule une fenêtre de maintenance préventive"""
        # Maintenance préventive: dimanche 2h-4h
        now = timezone.now()
        days_ahead = 6 - now.weekday()  # Dimanche
        if days_ahead <= 0:
            days_ahead += 7
        
        maintenance_time = now + timedelta(days=days_ahead)
        maintenance_time = maintenance_time.replace(hour=2, minute=0, second=0, microsecond=0)
        
        return maintenance_time.isoformat()
    
    def _calculate_corrective_window(self) -> str:
        """Calcule une fenêtre de maintenance corrective"""
        # Maintenance corrective: dans les 4 prochaines heures
        now = timezone.now()
        maintenance_time = now + timedelta(hours=4)
        
        return maintenance_time.isoformat()
    
    def _log_prediction_results(self, results: Dict[str, Any]):
        """Log les résultats de prédiction"""
        try:
            log_entry = {
                'timestamp': results.get('timestamp'),
                'duration_seconds': results.get('duration_seconds', 0),
                'predictions_count': len(results.get('predictions', [])),
                'anomalies_count': len(results.get('anomalies', [])),
                'recommendations_count': len(results.get('maintenance_recommendations', []))
            }
            
            self.prediction_history.append(log_entry)
            
            # Garder seulement les 50 dernières entrées
            if len(self.prediction_history) > 50:
                self.prediction_history = self.prediction_history[-50:]
            
            logger.info(f"Prédiction loggée: {log_entry}")
            
        except Exception as e:
            logger.error(f"Erreur log prédiction: {e}")
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """Récupère le statut de maintenance"""
        try:
            return {
                'last_prediction': self.prediction_history[-1] if self.prediction_history else None,
                'total_predictions': len(self.prediction_history),
                'scheduled_maintenance': self.maintenance_schedule,
                'config': self.maintenance_config,
                'next_analysis': timezone.now() + timedelta(hours=6).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur statut maintenance: {e}")
            return {'error': str(e)}

# Instance globale
predictive_maintenance = PredictiveMaintenance()
