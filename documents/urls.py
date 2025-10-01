from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Liste et création de documents
    path('', views.DocumentListCreateView.as_view(), name='document-list-create'),
    
    # Détail, modification et suppression d'un document
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    
    # Téléchargement d'un document
    path('<int:pk>/download/', views.document_download, name='document-download'),
    
    # Visualisation d'un document
    path('<int:pk>/view/', views.document_view, name='document-view'),
    
    # Statistiques
    path('stats/', views.document_stats, name='document-stats'),
    
    # Catégories
    path('categories/', views.document_categories, name='document-categories'),
    
    # Actions en lot
    path('bulk-delete/', views.document_bulk_delete, name='document-bulk-delete'),
    
    # ===== DOSSIERS =====
    # Liste et création de dossiers
    path('folders/', views.DocumentFolderListCreateView.as_view(), name='folder-list-create'),
    
    # Détail, modification et suppression d'un dossier
    path('folders/<int:pk>/', views.DocumentFolderDetailView.as_view(), name='folder-detail'),
    
    # Arbre des dossiers
    path('folders/tree/', views.document_folders_tree, name='folder-tree'),
    
    # Statistiques des dossiers
    path('folders/stats/', views.document_folders_stats, name='folder-stats'),
]
