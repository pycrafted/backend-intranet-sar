from django.urls import path
from . import views

app_name = 'annuaire'

urlpatterns = [
    # Départements
    path('departments/', views.DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    
    # Employés
    path('employees/', views.EmployeeListCreateView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/search/', views.employee_search, name='employee-search'),
    
    
    # Statistiques
    path('statistics/departments/', views.department_statistics, name='department-statistics'),
    
    # ===== NOUVELLES URLs OPTIMISÉES POUR L'ANNUAIRE =====
    # Endpoints utilisant les données de l'app authentication (LEGACY - à supprimer)
    path('users/', views.AnnuaireUserListView.as_view(), name='annuaire-user-list'),
    path('users/search/', views.annuaire_user_search, name='annuaire-user-search'),
    path('users/<int:user_id>/', views.annuaire_user_detail, name='annuaire-user-detail'),
    path('departments-list/', views.annuaire_departments_list, name='annuaire-departments-list'),
    path('statistics/', views.annuaire_statistics, name='annuaire-statistics'),
    path('hierarchy-data/', views.annuaire_hierarchy_data, name='annuaire-hierarchy-data'),
    
    # ===== ENDPOINTS ORGANIGRAMME/ANNUAIRE CORRIGÉS =====
    # Utiliser les modèles annuaire au lieu des modèles authentication
    path('departments-list-corrected/', views.department_list_for_annuaire, name='department-list-annuaire'),
    path('hierarchy-data-corrected/', views.employee_hierarchy_data, name='employee-hierarchy-data'),
]
