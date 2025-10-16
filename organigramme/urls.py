from django.urls import path
from . import views

app_name = 'organigramme'

urlpatterns = [
    # Directions
    path('directions/', views.DirectionListView.as_view(), name='direction-list'),
    path('directions/<int:pk>/', views.DirectionDetailView.as_view(), name='direction-detail'),
    
    # Agents
    path('agents/', views.AgentListView.as_view(), name='agent-list'),
    path('agents/<int:pk>/', views.AgentDetailView.as_view(), name='agent-detail'),
    path('agents/search/', views.agent_search_view, name='agent-search'),
    path('agents/<int:agent_id>/subordinates/', views.agent_subordinates_view, name='agent-subordinates'),
    path('agents/<int:agent_id>/avatar/', views.upload_agent_avatar, name='agent-avatar-upload'),
    
    # Directions et agents
    path('directions/<str:direction_name>/agents/', views.direction_agents_view, name='direction-agents'),
    
    # Arborescence
    path('tree/', views.agent_tree_view, name='agent-tree'),
    
    # Hiérarchie
    path('hierarchy/', views.hierarchy_info_view, name='hierarchy-info'),
    path('hierarchy/agent/<int:agent_id>/', views.agent_hierarchy_detail_view, name='agent-hierarchy-detail'),
    path('hierarchy/tree/', views.hierarchy_tree_view, name='hierarchy-tree'),
    path('hierarchy/rebuild/', views.rebuild_hierarchy_view, name='rebuild-hierarchy'),
    path('hierarchy/stats/', views.hierarchy_stats_view, name='hierarchy-stats'),
]
