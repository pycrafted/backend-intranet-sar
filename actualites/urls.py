from django.urls import path
from . import views

urlpatterns = [
    # Liste des articles avec filtrage et recherche
    path('', views.ArticleListAPIView.as_view(), name='article-list'),
    
    # Détail d'un article
    path('<int:pk>/', views.ArticleDetailAPIView.as_view(), name='article-detail'),
    
    # Créer un nouvel article
    path('create/', views.create_article, name='create-article'),
    
    
    # Statistiques des filtres
    path('stats/', views.article_stats, name='article-stats'),
]

