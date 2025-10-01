from django.urls import path
from . import views

urlpatterns = [
    # Endpoints pour les données de sécurité
    path('safety/', views.SafetyDataListAPIView.as_view(), name='safety-data-list'),
    path('safety/current/', views.safety_data_current, name='safety-data-current'),
    path('safety/update/', views.safety_data_update, name='safety-data-update'),
    path('safety/reset/', views.safety_data_reset, name='safety-data-reset'),
    path('safety/<int:pk>/', views.SafetyDataDetailAPIView.as_view(), name='safety-data-detail'),
    path('safety/<int:pk>/update/', views.SafetyDataUpdateAPIView.as_view(), name='safety-data-update-detail'),
    
    # Endpoints pour les idées
    path('ideas/', views.IdeaListAPIView.as_view(), name='idea-list'),
    path('ideas/create/', views.IdeaCreateAPIView.as_view(), name='idea-create'),
    path('ideas/submit/', views.idea_submit, name='idea-submit'),
    path('ideas/departments/', views.idea_departments, name='idea-departments'),
    path('ideas/<int:pk>/', views.IdeaDetailAPIView.as_view(), name='idea-detail'),
    path('ideas/<int:pk>/update/', views.IdeaUpdateAPIView.as_view(), name='idea-update'),
    path('ideas/<int:pk>/delete/', views.IdeaDeleteAPIView.as_view(), name='idea-delete'),
    
    # Endpoints pour le menu
    path('menu/items/', views.MenuItemListAPIView.as_view(), name='menu-item-list'),
    path('menu/items/<int:pk>/', views.MenuItemDetailAPIView.as_view(), name='menu-item-detail'),
    path('menu/days/', views.DayMenuListAPIView.as_view(), name='day-menu-list'),
    path('menu/days/<int:pk>/', views.DayMenuDetailAPIView.as_view(), name='day-menu-detail'),
    path('menu/week/', views.week_menu, name='week-menu'),
    path('menu/available-items/', views.available_menu_items, name='available-menu-items'),
    path('menu/create-week/', views.create_week_menu, name='create-week-menu'),
    
    # Endpoints pour les événements
    path('events/', views.EventListAPIView.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetailAPIView.as_view(), name='event-detail'),
    path('events/month/<int:year>/<int:month>/', views.events_by_month, name='events-by-month'),
    path('events/date/<str:date>/', views.events_by_date, name='events-by-date'),
    path('events/next/', views.next_event, name='next-event'),
    path('events/stats/', views.event_stats, name='event-stats'),
    
    # Endpoints pour les questionnaires
    path('questionnaires/', views.QuestionnaireListAPIView.as_view(), name='questionnaire-list'),
    path('questionnaires/active/', views.active_questionnaires, name='active-questionnaires'),
    path('questionnaires/statistics/', views.questionnaire_statistics, name='questionnaire-statistics'),
    path('questionnaires/<int:pk>/', views.QuestionnaireDetailAPIView.as_view(), name='questionnaire-detail'),
    path('questionnaires/create/', views.QuestionnaireCreateAPIView.as_view(), name='questionnaire-create'),
    path('questionnaires/<int:pk>/update/', views.QuestionnaireUpdateAPIView.as_view(), name='questionnaire-update'),
    path('questionnaires/<int:pk>/delete/', views.QuestionnaireDeleteAPIView.as_view(), name='questionnaire-delete'),
    path('questionnaires/<int:pk>/stats/', views.questionnaire_stats, name='questionnaire-stats'),
    path('questionnaires/<int:pk>/analytics/', views.questionnaire_analytics, name='questionnaire-analytics'),
    path('questionnaires/<int:pk>/export/', views.questionnaire_export, name='questionnaire-export'),
    path('questionnaires/<int:pk>/duplicate/', views.questionnaire_duplicate, name='questionnaire-duplicate'),
    path('questionnaires/<int:pk>/status/', views.questionnaire_status_update, name='questionnaire-status-update'),
    
    # Endpoints pour les questions
    path('questionnaires/<int:questionnaire_id>/questions/', views.QuestionListAPIView.as_view(), name='question-list'),
    path('questionnaires/<int:questionnaire_id>/questions/create/', views.QuestionCreateAPIView.as_view(), name='question-create'),
    path('questions/<int:pk>/update/', views.QuestionUpdateAPIView.as_view(), name='question-update'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteAPIView.as_view(), name='question-delete'),
    
    # Endpoints pour les réponses
    path('questionnaires/<int:questionnaire_id>/responses/', views.QuestionnaireResponseListAPIView.as_view(), name='questionnaire-response-list'),
    path('questionnaires/<int:questionnaire_id>/responses/submit/', views.QuestionnaireResponseCreateAPIView.as_view(), name='questionnaire-response-submit'),
]
