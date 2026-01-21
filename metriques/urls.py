from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.MetricsSummaryView.as_view(), name='metrics-summary'),
    path('logins/', views.UserLoginListView.as_view(), name='user-login-list'),
    path('login-stats/', views.LoginStatsView.as_view(), name='login-stats'),
]
