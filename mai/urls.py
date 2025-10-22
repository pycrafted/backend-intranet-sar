from django.urls import path
from . import views
from . import optimization_views
from .hybrid_views import HybridSearchView, HybridContextView, ABTestingView, MonitoringView
from .deployment_views import (
    DeploymentStatusView, DeploymentControlView, RealTimeMetricsView,
    HistoricalMetricsView, ABTestResultsView, HealthCheckView,
    DeploymentRecommendationsView, SystemDashboardView,
    PerformanceOptimizationView, AlertManagementView
)
from .phase5_views import (
    AutoOptimizationView, PredictiveMaintenanceView, IntelligentAnalyticsView,
    Phase5DashboardView, PerformanceTuningView, DataQualityView,
    ScalabilityView, InsightsView
)
from .phase6_views import (
    cache_status, cache_optimize, cache_warm_up, cache_clear,
    index_status, index_build, index_optimize, index_reindex_if_needed, index_history,
    monitoring_metrics, monitoring_health, monitoring_report, monitoring_alerts,
    monitoring_acknowledge_alert, monitoring_cleanup,
    phase6_dashboard, optimization_recommendations
)

urlpatterns = [
    # Endpoints MAI existants (compatibilité)
    path('search/', views.search_question, name='mai_search'),
    path('context/', views.get_context, name='mai_context'),
    path('statistics/', views.get_statistics, name='mai_statistics'),
    path('sample-questions/', views.get_sample_questions, name='mai_sample_questions'),
    
    # Endpoints de messages de chargement intelligents
    path('loading-message/', views.get_loading_message, name='loading_message'),
    path('progressive-loading/', views.get_progressive_loading, name='progressive_loading'),
    path('quick-loading/', views.get_quick_loading_message, name='quick_loading'),
    
    # Nouveaux endpoints hybrides
    path('hybrid-search/', HybridSearchView.as_view(), name='hybrid_search'),
    path('hybrid-context/', HybridContextView.as_view(), name='hybrid_context'),
    path('ab-test/', ABTestingView.as_view(), name='ab_test'),
    path('monitoring/', MonitoringView.as_view(), name='monitoring'),
    
    # Endpoints Phase 4 - Déploiement et Monitoring
    path('deployment/status/', DeploymentStatusView.as_view(), name='deployment_status'),
    path('deployment/control/', DeploymentControlView.as_view(), name='deployment_control'),
    path('metrics/real-time/', RealTimeMetricsView.as_view(), name='real_time_metrics'),
    path('metrics/historical/', HistoricalMetricsView.as_view(), name='historical_metrics'),
    path('metrics/ab-test/', ABTestResultsView.as_view(), name='ab_test_results'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('recommendations/', DeploymentRecommendationsView.as_view(), name='deployment_recommendations'),
    path('dashboard/', SystemDashboardView.as_view(), name='system_dashboard'),
    path('optimization/', PerformanceOptimizationView.as_view(), name='performance_optimization'),
    path('alerts/', AlertManagementView.as_view(), name='alert_management'),
    
    # Endpoints Phase 5 - Optimisation et Maintenance Intelligente
    path('auto-optimization/', AutoOptimizationView.as_view(), name='auto_optimization'),
    path('predictive-maintenance/', PredictiveMaintenanceView.as_view(), name='predictive_maintenance'),
    path('intelligent-analytics/', IntelligentAnalyticsView.as_view(), name='intelligent_analytics'),
    path('phase5-dashboard/', Phase5DashboardView.as_view(), name='phase5_dashboard'),
    path('performance-tuning/', PerformanceTuningView.as_view(), name='performance_tuning'),
    path('data-quality/', DataQualityView.as_view(), name='data_quality'),
    path('scalability/', ScalabilityView.as_view(), name='scalability'),
    path('insights/', InsightsView.as_view(), name='insights'),
    
    # Endpoints Phase 6 - Optimisations Avancées
    # Cache Management
    path('cache/status/', cache_status, name='cache_status'),
    path('cache/optimize/', cache_optimize, name='cache_optimize'),
    path('cache/warm-up/', cache_warm_up, name='cache_warm_up'),
    path('cache/clear/', cache_clear, name='cache_clear'),
    
    # Vector Index Optimization
    path('index/status/', index_status, name='index_status'),
    path('index/build/', index_build, name='index_build'),
    path('index/optimize/', index_optimize, name='index_optimize'),
    path('index/reindex-check/', index_reindex_if_needed, name='index_reindex_check'),
    path('index/history/', index_history, name='index_history'),
    
    # Advanced Monitoring
    path('monitoring/metrics/', monitoring_metrics, name='monitoring_metrics'),
    path('monitoring/health/', monitoring_health, name='monitoring_health'),
    path('monitoring/report/', monitoring_report, name='monitoring_report'),
    path('monitoring/alerts/', monitoring_alerts, name='monitoring_alerts'),
    path('monitoring/acknowledge-alert/', monitoring_acknowledge_alert, name='monitoring_acknowledge_alert'),
    path('monitoring/cleanup/', monitoring_cleanup, name='monitoring_cleanup'),
    
    # Phase 6 Dashboard and Recommendations
    path('phase6-dashboard/', phase6_dashboard, name='phase6_dashboard'),
    path('optimization-recommendations/', optimization_recommendations, name='optimization_recommendations'),
    
    # Endpoints d'optimisation intelligente Phase 6
    path('intelligent-optimization/run/', optimization_views.run_comprehensive_optimization, name='run_comprehensive_optimization'),
    path('intelligent-optimization/status/', optimization_views.get_optimization_status, name='get_optimization_status'),
    path('intelligent-optimization/cache/', optimization_views.optimize_cache, name='optimize_cache'),
    path('intelligent-optimization/indexes/', optimization_views.optimize_vector_indexes, name='optimize_vector_indexes'),
    path('intelligent-optimization/cache-stats/', optimization_views.get_cache_stats, name='get_cache_stats'),
    path('intelligent-optimization/index-performance/', optimization_views.get_index_performance, name='get_index_performance'),
    path('intelligent-optimization/system-health/', optimization_views.get_system_health, name='get_system_health'),
    path('intelligent-optimization/schedule/', optimization_views.schedule_automatic_optimization, name='schedule_automatic_optimization'),
    path('intelligent-optimization/clear-cache/', optimization_views.clear_cache, name='clear_cache'),
    path('intelligent-optimization/history/', optimization_views.get_optimization_history, name='get_optimization_history'),
]
