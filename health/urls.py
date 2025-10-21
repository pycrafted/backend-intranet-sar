"""
URLs de santé du système.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
]