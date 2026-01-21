from rest_framework import serializers
from .models import UserLogin, AppMetric
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLoginSerializer(serializers.ModelSerializer):
    """Serializer pour les connexions utilisateurs"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = UserLogin
        fields = [
            'id', 'user', 'user_email', 'user_name', 'department_name',
            'login_time', 'logout_time', 'session_duration',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'login_time']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_department_name(self, obj):
        return obj.user.department.name if obj.user.department else None


class AppMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques de l'application"""
    
    class Meta:
        model = AppMetric
        fields = ['id', 'metric_type', 'value', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']


class MetricsSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des métriques"""
    daily_logins = serializers.IntegerField()
    weekly_logins = serializers.IntegerField()
    monthly_logins = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    active_users_month = serializers.IntegerField()
    total_articles = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    total_forum_posts = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    login_trend_daily = serializers.ListField(child=serializers.DictField())
    login_trend_weekly = serializers.ListField(child=serializers.DictField())
    login_trend_monthly = serializers.ListField(child=serializers.DictField())
    login_trend_yearly = serializers.ListField(child=serializers.DictField())
    top_users = serializers.ListField(child=serializers.DictField())
    # Nouvelles métriques
    avg_session_duration_minutes = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    hourly_logins = serializers.ListField(child=serializers.DictField())
    weekday_activity = serializers.ListField(child=serializers.DictField())
    department_stats = serializers.ListField(child=serializers.DictField())
    top_documents = serializers.ListField(child=serializers.DictField())
    new_users_count = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
