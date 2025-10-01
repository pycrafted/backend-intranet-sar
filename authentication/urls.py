from django.urls import path
from . import views

urlpatterns = [
    # Authentification de base
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    path('current-user/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Gestion du profil
    path('profile/', views.CurrentUserView.as_view(), name='user-profile'),
    path('change-password/', views.UserLogoutView.as_view(), name='change-password'),
    
    # Token CSRF
    path('csrf/', views.get_csrf_token, name='get-csrf-token'),
    
    # Avatar
    path('upload-avatar/', views.upload_avatar, name='upload-avatar'),
    
    # Vérification d'authentification
    path('check-auth/', views.check_auth_status, name='check-auth'),
    
    # Liste des utilisateurs
    path('users/', views.UserListView.as_view(), name='user-list'),
    
    # OAuth 2.0 Google
    path('google/auth-url/', views.google_auth_url, name='google-auth-url'),
    path('google/callback/', views.google_auth_callback, name='google-auth-callback'),
    path('google/disconnect/', views.google_disconnect, name='google-disconnect'),
    path('google/status/', views.google_status, name='google-status'),
    path('google/get-auth-url/', views.get_google_auth_url, name='get-google-auth-url'),
    
]
