from django.urls import path
from . import views

urlpatterns = [
    # Authentification de base
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    path('current-user/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Token CSRF
    path('csrf/', views.get_csrf_token, name='get-csrf-token'),
    
    # Liste des utilisateurs
    path('users/', views.UserListView.as_view(), name='user-list'),
    # Admin - gestion des utilisateurs
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/groups/', views.AdminUserGroupsView.as_view(), name='admin-user-groups'),
    path('admin/users/<int:user_id>/reset-password/', views.AdminUserResetPasswordView.as_view(), name='admin-user-reset-password'),
]
