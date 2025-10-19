from django.urls import path
from . import views
from . import test_views

urlpatterns = [
    # Liste des articles avec filtrage et recherche
    path('', views.ArticleListAPIView.as_view(), name='article-list'),
    
    # Détail d'un article
    path('<int:pk>/', views.ArticleDetailAPIView.as_view(), name='article-detail'),
    
    # Créer un nouvel article
    path('create/', views.create_article, name='create-article'),
    
    
    # Statistiques des filtres
    path('stats/', views.article_stats, name='article-stats'),
    
    # Endpoints de test
    path('test/images/', test_views.test_images_endpoint, name='test-images'),
    path('test/images/<str:image_name>/', test_views.test_single_image, name='test-single-image'),
]

