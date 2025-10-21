"""
Système d'analytics intelligents pour la Phase 5.
Fournit des insights automatiques et des recommandations intelligentes.
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

class IntelligentAnalytics:
    """Système d'analytics intelligents"""
    
    def __init__(self):
        self.analytics_config = self._load_analytics_config()
        self.insights_history = []
        self.patterns_cache = {}
        
    def _load_analytics_config(self) -> Dict[str, Any]:
        """Charge la configuration des analytics"""
        return {
            'analysis': {
                'lookback_days': 30,
                'trend_analysis_days': 7,
                'pattern_detection_enabled': True,
                'correlation_analysis_enabled': True
            },
            'insights': {
                'auto_generation_enabled': True,
                'insight_confidence_threshold': 0.7,
                'pattern_significance_threshold': 0.8,
                'correlation_threshold': 0.6
            },
            'recommendations': {
                'auto_recommendations_enabled': True,
                'recommendation_priority_threshold': 0.8,
                'action_impact_threshold': 0.5
            }
        }
    
    def run_intelligent_analysis(self) -> Dict[str, Any]:
        """Exécute une analyse intelligente complète"""
        start_time = time.time()
        analysis_results = {
            'timestamp': timezone.now().isoformat(),
            'duration_seconds': 0,
            'insights': [],
            'patterns': [],
            'correlations': [],
            'recommendations': [],
            'trends': {},
            'anomalies': [],
            'predictions': []
        }
        
        try:
            logger.info("Démarrage de l'analyse intelligente")
            
            # 1. Analyse des tendances
            trends = self._analyze_comprehensive_trends()
            analysis_results['trends'] = trends
            
            # 2. Détection de patterns
            patterns = self._detect_patterns()
            analysis_results['patterns'] = patterns
            
            # 3. Analyse de corrélations
            correlations = self._analyze_correlations()
            analysis_results['correlations'] = correlations
            
            # 4. Génération d'insights
            insights = self._generate_insights(analysis_results)
            analysis_results['insights'] = insights
            
            # 5. Détection d'anomalies
            anomalies = self._detect_intelligent_anomalies()
            analysis_results['anomalies'] = anomalies
            
            # 6. Prédictions intelligentes
            predictions = self._generate_intelligent_predictions(analysis_results)
            analysis_results['predictions'] = predictions
            
            # 7. Recommandations intelligentes
            recommendations = self._generate_intelligent_recommendations(analysis_results)
            analysis_results['recommendations'] = recommendations
            
            # Calculer la durée
            analysis_results['duration_seconds'] = time.time() - start_time
            
            # Logger les résultats
            self._log_analytics_results(analysis_results)
            
            logger.info(f"Analyse intelligente terminée en {analysis_results['duration_seconds']:.2f}s")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse intelligente: {e}")
            analysis_results['error'] = str(e)
            return analysis_results
    
    def _analyze_comprehensive_trends(self) -> Dict[str, Any]:
        """Analyse complète des tendances"""
        try:
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=self.analytics_config['analysis']['lookback_days'])
            
            # Récupérer les données
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            ).order_by('created_at')
            
            # Tendances de performance
            performance_trends = self._analyze_performance_trends(logs)
            
            # Tendances d'utilisation
            usage_trends = self._analyze_usage_trends(logs)
            
            # Tendances de qualité
            quality_trends = self._analyze_quality_trends(logs)
            
            # Tendances temporelles
            temporal_trends = self._analyze_temporal_trends(logs)
            
            # Tendances par méthode
            method_trends = self._analyze_method_trends(logs)
            
            return {
                'performance_trends': performance_trends,
                'usage_trends': usage_trends,
                'quality_trends': quality_trends,
                'temporal_trends': temporal_trends,
                'method_trends': method_trends,
                'overall_trend_direction': self._calculate_overall_trend_direction(
                    performance_trends, usage_trends, quality_trends
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances: {e}")
            return {'error': str(e)}
    
    def _detect_patterns(self) -> List[Dict[str, Any]]:
        """Détecte les patterns dans les données"""
        try:
            patterns = []
            
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=7)  # Dernière semaine
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            # Pattern 1: Patterns temporels
            temporal_patterns = self._detect_temporal_patterns(logs)
            patterns.extend(temporal_patterns)
            
            # Pattern 2: Patterns de performance
            performance_patterns = self._detect_performance_patterns(logs)
            patterns.extend(performance_patterns)
            
            # Pattern 3: Patterns d'utilisation
            usage_patterns = self._detect_usage_patterns(logs)
            patterns.extend(usage_patterns)
            
            # Pattern 4: Patterns de qualité
            quality_patterns = self._detect_quality_patterns(logs)
            patterns.extend(quality_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Erreur détection patterns: {e}")
            return []
    
    def _analyze_correlations(self) -> List[Dict[str, Any]]:
        """Analyse les corrélations entre variables"""
        try:
            correlations = []
            
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=7)
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            # Corrélation 1: Temps de réponse vs Taux de succès
            response_success_correlation = self._analyze_response_success_correlation(logs)
            if response_success_correlation:
                correlations.append(response_success_correlation)
            
            # Corrélation 2: Heure vs Performance
            time_performance_correlation = self._analyze_time_performance_correlation(logs)
            if time_performance_correlation:
                correlations.append(time_performance_correlation)
            
            # Corrélation 3: Méthode vs Qualité
            method_quality_correlation = self._analyze_method_quality_correlation(logs)
            if method_quality_correlation:
                correlations.append(method_quality_correlation)
            
            # Corrélation 4: Charge vs Ressources
            load_resource_correlation = self._analyze_load_resource_correlation()
            if load_resource_correlation:
                correlations.append(load_resource_correlation)
            
            return correlations
            
        except Exception as e:
            logger.error(f"Erreur analyse corrélations: {e}")
            return []
    
    def _generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des insights automatiques"""
        try:
            insights = []
            
            # Insight 1: Performance
            performance_insights = self._generate_performance_insights(analysis_results)
            insights.extend(performance_insights)
            
            # Insight 2: Utilisation
            usage_insights = self._generate_usage_insights(analysis_results)
            insights.extend(usage_insights)
            
            # Insight 3: Qualité
            quality_insights = self._generate_quality_insights(analysis_results)
            insights.extend(quality_insights)
            
            # Insight 4: Efficacité
            efficiency_insights = self._generate_efficiency_insights(analysis_results)
            insights.extend(efficiency_insights)
            
            # Insight 5: Opportunités
            opportunity_insights = self._generate_opportunity_insights(analysis_results)
            insights.extend(opportunity_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Erreur génération insights: {e}")
            return []
    
    def _detect_intelligent_anomalies(self) -> List[Dict[str, Any]]:
        """Détecte les anomalies de manière intelligente"""
        try:
            anomalies = []
            
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(days=7)
            
            logs = RAGSearchLog.objects.filter(
                created_at__range=(start_time, end_time)
            )
            
            # Anomalie 1: Dégradation de performance
            performance_anomalies = self._detect_performance_anomalies(logs)
            anomalies.extend(performance_anomalies)
            
            # Anomalie 2: Changements d'utilisation
            usage_anomalies = self._detect_usage_anomalies(logs)
            anomalies.extend(usage_anomalies)
            
            # Anomalie 3: Problèmes de qualité
            quality_anomalies = self._detect_quality_anomalies(logs)
            anomalies.extend(quality_anomalies)
            
            # Anomalie 4: Anomalies systémiques
            system_anomalies = self._detect_system_anomalies()
            anomalies.extend(system_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies intelligentes: {e}")
            return []
    
    def _generate_intelligent_predictions(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des prédictions intelligentes"""
        try:
            predictions = []
            
            # Prédiction 1: Charge future
            load_predictions = self._predict_future_load(analysis_results)
            predictions.extend(load_predictions)
            
            # Prédiction 2: Performance future
            performance_predictions = self._predict_future_performance(analysis_results)
            predictions.extend(performance_predictions)
            
            # Prédiction 3: Besoins en ressources
            resource_predictions = self._predict_resource_needs(analysis_results)
            predictions.extend(resource_predictions)
            
            # Prédiction 4: Évolutions de qualité
            quality_predictions = self._predict_quality_evolution(analysis_results)
            predictions.extend(quality_predictions)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur génération prédictions intelligentes: {e}")
            return []
    
    def _generate_intelligent_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des recommandations intelligentes"""
        try:
            recommendations = []
            
            # Recommandations basées sur les insights
            insights = analysis_results.get('insights', [])
            for insight in insights:
                if insight.get('confidence', 0) > self.analytics_config['insights']['insight_confidence_threshold']:
                    recommendation = self._generate_insight_based_recommendation(insight)
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Recommandations basées sur les patterns
            patterns = analysis_results.get('patterns', [])
            for pattern in patterns:
                if pattern.get('significance', 0) > self.analytics_config['insights']['pattern_significance_threshold']:
                    recommendation = self._generate_pattern_based_recommendation(pattern)
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Recommandations basées sur les corrélations
            correlations = analysis_results.get('correlations', [])
            for correlation in correlations:
                if correlation.get('strength', 0) > self.analytics_config['insights']['correlation_threshold']:
                    recommendation = self._generate_correlation_based_recommendation(correlation)
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Recommandations basées sur les anomalies
            anomalies = analysis_results.get('anomalies', [])
            for anomaly in anomalies:
                if anomaly.get('severity') in ['high', 'critical']:
                    recommendation = self._generate_anomaly_based_recommendation(anomaly)
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Trier par priorité
            recommendations.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations intelligentes: {e}")
            return []
    
    # Méthodes d'analyse spécifiques
    def _analyze_performance_trends(self, logs) -> Dict[str, Any]:
        """Analyse les tendances de performance"""
        try:
            # Analyser par jour
            daily_performance = {}
            current_date = logs.first().created_at.date() if logs.exists() else timezone.now().date()
            end_date = logs.last().created_at.date() if logs.exists() else timezone.now().date()
            
            while current_date <= end_date:
                day_logs = logs.filter(created_at__date=current_date)
                if day_logs.exists():
                    daily_performance[str(current_date)] = {
                        'avg_response_time': day_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0,
                        'success_rate': day_logs.filter(success=True).count() / day_logs.count(),
                        'total_searches': day_logs.count()
                    }
                current_date += timedelta(days=1)
            
            # Calculer les tendances
            if len(daily_performance) > 1:
                dates = sorted(daily_performance.keys())
                response_times = [daily_performance[d]['avg_response_time'] for d in dates]
                success_rates = [daily_performance[d]['success_rate'] for d in dates]
                
                # Tendance des temps de réponse
                response_trend = self._calculate_trend_direction(response_times)
                
                # Tendance des taux de succès
                success_trend = self._calculate_trend_direction(success_rates)
                
                return {
                    'daily_performance': daily_performance,
                    'response_time_trend': response_trend,
                    'success_rate_trend': success_trend,
                    'overall_trend': 'improving' if response_trend == 'decreasing' and success_trend == 'increasing' else 'degrading'
                }
            
            return {'daily_performance': daily_performance}
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances performance: {e}")
            return {}
    
    def _detect_temporal_patterns(self, logs) -> List[Dict[str, Any]]:
        """Détecte les patterns temporels"""
        try:
            patterns = []
            
            # Pattern par heure
            hourly_stats = {}
            for hour in range(24):
                hour_logs = logs.filter(created_at__hour=hour)
                if hour_logs.exists():
                    hourly_stats[hour] = {
                        'count': hour_logs.count(),
                        'avg_response_time': hour_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0,
                        'success_rate': hour_logs.filter(success=True).count() / hour_logs.count()
                    }
            
            # Détecter les heures de pointe
            if hourly_stats:
                max_count = max(hourly_stats.values(), key=lambda x: x['count'])['count']
                peak_hours = [h for h, stats in hourly_stats.items() if stats['count'] > max_count * 0.8]
                
                if peak_hours:
                    patterns.append({
                        'type': 'peak_hours',
                        'pattern': 'Les heures de pointe sont: ' + ', '.join(map(str, peak_hours)),
                        'significance': 0.8,
                        'impact': 'high',
                        'description': f'Pic d\'utilisation détecté aux heures {peak_hours}'
                    })
            
            # Pattern par jour de la semaine
            weekday_stats = {}
            for day in range(7):
                day_logs = logs.filter(created_at__week_day=day)
                if day_logs.exists():
                    weekday_stats[day] = {
                        'count': day_logs.count(),
                        'avg_response_time': day_logs.aggregate(
                            avg_time=models.Avg('response_time_ms')
                        )['avg_time'] or 0
                    }
            
            # Détecter les jours de faible activité
            if weekday_stats:
                min_count = min(weekday_stats.values(), key=lambda x: x['count'])['count']
                low_activity_days = [d for d, stats in weekday_stats.items() if stats['count'] < min_count * 1.2]
                
                if low_activity_days:
                    patterns.append({
                        'type': 'low_activity_days',
                        'pattern': f'Jours de faible activité: {low_activity_days}',
                        'significance': 0.7,
                        'impact': 'medium',
                        'description': f'Activité réduite détectée les jours {low_activity_days}'
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Erreur détection patterns temporels: {e}")
            return []
    
    def _analyze_response_success_correlation(self, logs) -> Optional[Dict[str, Any]]:
        """Analyse la corrélation entre temps de réponse et taux de succès"""
        try:
            # Grouper par tranches de temps de réponse
            response_ranges = [
                (0, 100, 'très rapide'),
                (100, 500, 'rapide'),
                (500, 1000, 'moyen'),
                (1000, 2000, 'lent'),
                (2000, float('inf'), 'très lent')
            ]
            
            correlations = []
            for min_time, max_time, label in response_ranges:
                range_logs = logs.filter(
                    response_time_ms__gte=min_time,
                    response_time_ms__lt=max_time
                )
                
                if range_logs.exists():
                    success_rate = range_logs.filter(success=True).count() / range_logs.count()
                    correlations.append({
                        'range': label,
                        'success_rate': success_rate,
                        'count': range_logs.count()
                    })
            
            # Calculer la corrélation
            if len(correlations) > 1:
                # Corrélation simplifiée
                fast_success = correlations[0]['success_rate'] if correlations else 0
                slow_success = correlations[-1]['success_rate'] if correlations else 0
                correlation_strength = abs(fast_success - slow_success)
                
                return {
                    'type': 'response_success_correlation',
                    'strength': correlation_strength,
                    'direction': 'negative' if fast_success > slow_success else 'positive',
                    'description': f'Corrélation entre temps de réponse et succès: {correlation_strength:.2f}',
                    'details': correlations
                }
            
        except Exception as e:
            logger.error(f"Erreur analyse corrélation réponse-succès: {e}")
            return None
    
    def _generate_performance_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des insights sur les performances"""
        try:
            insights = []
            
            trends = analysis_results.get('trends', {})
            performance_trends = trends.get('performance_trends', {})
            
            if performance_trends:
                response_trend = performance_trends.get('response_time_trend', 'stable')
                success_trend = performance_trends.get('success_rate_trend', 'stable')
                
                if response_trend == 'decreasing' and success_trend == 'increasing':
                    insights.append({
                        'type': 'performance_improvement',
                        'title': 'Amélioration des performances détectée',
                        'description': 'Les temps de réponse diminuent et le taux de succès augmente',
                        'confidence': 0.9,
                        'impact': 'positive',
                        'recommendation': 'Continuer les optimisations actuelles'
                    })
                elif response_trend == 'increasing' and success_trend == 'decreasing':
                    insights.append({
                        'type': 'performance_degradation',
                        'title': 'Dégradation des performances détectée',
                        'description': 'Les temps de réponse augmentent et le taux de succès diminue',
                        'confidence': 0.9,
                        'impact': 'negative',
                        'recommendation': 'Investiguer les causes et optimiser le système'
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Erreur génération insights performance: {e}")
            return []
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calcule la direction d'une tendance"""
        if len(values) < 2:
            return 'stable'
        
        # Calculer la pente
        n = len(values)
        x = list(range(n))
        y = values
        
        # Régression linéaire simple
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _log_analytics_results(self, results: Dict[str, Any]):
        """Log les résultats d'analytics"""
        try:
            log_entry = {
                'timestamp': results.get('timestamp'),
                'duration_seconds': results.get('duration_seconds', 0),
                'insights_count': len(results.get('insights', [])),
                'patterns_count': len(results.get('patterns', [])),
                'correlations_count': len(results.get('correlations', [])),
                'recommendations_count': len(results.get('recommendations', []))
            }
            
            self.insights_history.append(log_entry)
            
            # Garder seulement les 100 dernières entrées
            if len(self.insights_history) > 100:
                self.insights_history = self.insights_history[-100:]
            
            logger.info(f"Analytics loggés: {log_entry}")
            
        except Exception as e:
            logger.error(f"Erreur log analytics: {e}")
    
    def get_analytics_status(self) -> Dict[str, Any]:
        """Récupère le statut des analytics"""
        try:
            return {
                'last_analysis': self.insights_history[-1] if self.insights_history else None,
                'total_analyses': len(self.insights_history),
                'config': self.analytics_config,
                'next_analysis': timezone.now() + timedelta(hours=6).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur statut analytics: {e}")
            return {'error': str(e)}

# Instance globale
intelligent_analytics = IntelligentAnalytics()
