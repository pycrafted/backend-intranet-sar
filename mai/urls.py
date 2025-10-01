from django.urls import path
from . import views

urlpatterns = [
    # Endpoints MAI
    path('search/', views.search_question, name='mai_search'),
    path('context/', views.get_context, name='mai_context'),
    path('statistics/', views.get_statistics, name='mai_statistics'),
    path('sample-questions/', views.get_sample_questions, name='mai_sample_questions'),
]
