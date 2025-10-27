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
]
