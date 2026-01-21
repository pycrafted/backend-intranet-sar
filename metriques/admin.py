from django.contrib import admin
from .models import UserLogin, AppMetric


@admin.register(UserLogin)
class UserLoginAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'session_duration', 'ip_address']
    list_filter = ['login_time', 'user']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'ip_address']
    readonly_fields = ['login_time', 'session_duration']
    date_hierarchy = 'login_time'


@admin.register(AppMetric)
class AppMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'date', 'created_at']
    list_filter = ['metric_type', 'date']
    search_fields = ['metric_type']
    date_hierarchy = 'date'
