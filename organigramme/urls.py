from django.urls import path
from . import views

app_name = 'organigramme'

urlpatterns = [
    # Directions
    path('directions/', views.DirectionListView.as_view(), name='direction-list'),
    
    # Agents
    path('agents/', views.AgentListView.as_view(), name='agent-list'),
    path('agents/<int:pk>/', views.AgentDetailView.as_view(), name='agent-detail'),
    path('agents/search/', views.agent_search_view, name='agent-search'),
    path('agents/<int:agent_id>/subordinates/', views.agent_subordinates_view, name='agent-subordinates'),
    path('agents/<int:agent_id>/avatar/', views.upload_agent_avatar, name='agent-avatar-upload'),
    
    # Directions et agents
    path('directions/<str:direction_slug>/agents/', views.direction_agents_view, name='direction-agents'),
    
    # Arborescence
    path('tree/', views.agent_tree_view, name='agent-tree'),
]
