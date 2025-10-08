from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.conf import settings
import os

from .models import Document, DocumentCategory, DocumentFolder
from .serializers import (
    DocumentSerializer, 
    DocumentListSerializer, 
    DocumentUploadSerializer, 
    DocumentCategorySerializer,
    DocumentFolderSerializer,
    DocumentFolderTreeSerializer
)

class DocumentListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des documents
    GET: Liste tous les documents actifs
    POST: Créer un nouveau document
    """
    permission_classes = []  # Authentification temporairement désactivée
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create pour gérer l'upload"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            raise
    
    def get_queryset(self):
        """Retourne tous les documents actifs"""
        queryset = Document.objects.filter(is_active=True)
        
        # Filtrage par recherche
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(uploaded_by__first_name__icontains=search) |
                Q(uploaded_by__last_name__icontains=search)
            )
        
        # Filtrage par catégorie
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtrage par dossier
        folder_id = self.request.query_params.get('folder', None)
        if folder_id is not None:
            if folder_id == 'null' or folder_id == '':
                queryset = queryset.filter(folder__isnull=True)
            else:
                queryset = queryset.filter(folder_id=folder_id)
        
        # Tri
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def perform_create(self, serializer):
        """Créer un nouveau document"""
        # Calculer la taille du fichier avant de sauvegarder
        file = self.request.FILES.get('file')
        if not file:
            raise serializers.ValidationError("Aucun fichier fourni")
        
        file_size = file.size
        
        
        # La catégorie est maintenant optionnelle
        category_id = self.request.data.get('category')
        category = None
        if category_id:
            try:
                category_id = int(category_id)
                category = DocumentCategory.objects.filter(id=category_id, is_active=True).first()
            except (ValueError, TypeError):
                pass
        
        # Gérer le dossier (optionnel)
        folder_id = self.request.data.get('folder')
        folder = None
        if folder_id and folder_id != 'null' and folder_id != '':
            try:
                folder_id = int(folder_id)
                folder = DocumentFolder.objects.filter(id=folder_id, is_active=True).first()
            except (ValueError, TypeError):
                pass
        
        # Utilisateur temporaire (authentification désactivée)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        default_user = User.objects.first()  # Prendre le premier utilisateur disponible
        
        if not default_user:
            # Créer un utilisateur par défaut si aucun n'existe
            default_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
        
        serializer.save(uploaded_by=default_user, file_size=file_size, category=category, folder=folder)

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, modifier et supprimer un document
    """
    permission_classes = [AllowAny]  # AUTHENTIFICATION DÉSACTIVÉE
    serializer_class = DocumentSerializer
    
    def get_queryset(self):
        return Document.objects.filter(is_active=True)

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_download(request, pk):
    """
    Télécharger un document PDF
    """
    try:
        document = get_object_or_404(Document, pk=pk, is_active=True)
        
        # Vérifier que le fichier existe
        if not document.file or not os.path.exists(document.file.path):
            raise Http404("Fichier non trouvé")
        
        # Incrémenter le compteur de téléchargements
        document.increment_download_count()
        
        # Lire le fichier
        with open(document.file.path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
            response['Content-Length'] = document.file_size
            return response
            
    except Http404:
        return Response(
            {'error': 'Fichier non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du téléchargement: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_view(request, pk):
    """
    Visualiser un document PDF dans le navigateur
    """
    try:
        document = get_object_or_404(Document, pk=pk, is_active=True)
        
        # Vérifier que le fichier existe
        if not document.file or not os.path.exists(document.file.path):
            raise Http404("Fichier non trouvé")
        
        # Vérifier que le fichier est un PDF
        if not document.is_pdf():
            return Response(
                {'error': 'La visualisation en ligne n\'est disponible que pour les documents PDF. Veuillez télécharger le fichier pour le consulter.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lire le fichier pour l'affichage
        with open(document.file.path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
            response['Content-Length'] = document.file_size
            return response
            
    except Http404:
        return Response(
            {'error': 'Fichier non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la visualisation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_stats(request):
    """
    Statistiques des documents
    """
    try:
        total_documents = Document.objects.filter(is_active=True).count()
        total_downloads = Document.objects.filter(is_active=True).aggregate(
            total=Sum('download_count')
        )['total'] or 0
        
        # Documents récents (7 derniers jours)
        from django.utils import timezone
        from datetime import timedelta
        recent_documents = Document.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_documents': total_documents,
            'total_downloads': total_downloads,
            'recent_documents': recent_documents,
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du calcul des statistiques: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_categories(request):
    """
    Liste des catégories de documents
    """
    try:
        categories = DocumentCategory.objects.filter(is_active=True).order_by('order', 'name')
        serializer = DocumentCategorySerializer(categories, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des catégories: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_bulk_delete(request):
    """
    Supprimer plusieurs documents en lot
    """
    try:
        document_ids = request.data.get('document_ids', [])
        
        if not document_ids:
            return Response(
                {'error': 'Aucun document sélectionné'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Supprimer les documents (soft delete)
        deleted_count = Document.objects.filter(
            id__in=document_ids,
            is_active=True
        ).update(is_active=False)
        
        return Response({
            'message': f'{deleted_count} document(s) supprimé(s) avec succès',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la suppression: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ===== VUES POUR LES DOSSIERS =====

class DocumentFolderListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des dossiers
    GET: Liste tous les dossiers actifs
    POST: Créer un nouveau dossier
    """
    permission_classes = [AllowAny]  # AUTHENTIFICATION DÉSACTIVÉE
    serializer_class = DocumentFolderSerializer
    
    def get_queryset(self):
        """Retourne tous les dossiers actifs"""
        queryset = DocumentFolder.objects.filter(is_active=True)
        
        # Filtrage par dossier parent
        parent_id = self.request.query_params.get('parent', None)
        if parent_id is not None:
            if parent_id == 'null' or parent_id == '':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        """Créer un nouveau dossier"""
        serializer.save(created_by=self.request.user)

class DocumentFolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, modifier et supprimer un dossier
    """
    permission_classes = [AllowAny]  # AUTHENTIFICATION DÉSACTIVÉE
    serializer_class = DocumentFolderSerializer
    
    def get_queryset(self):
        return DocumentFolder.objects.filter(is_active=True)

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_folders_tree(request):
    """
    Retourne l'arbre complet des dossiers
    """
    try:
        # Récupérer tous les dossiers racines (sans parent)
        root_folders = DocumentFolder.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('name')
        
        serializer = DocumentFolderTreeSerializer(root_folders, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération de l\'arbre: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def document_folders_stats(request):
    """
    Statistiques des dossiers
    """
    try:
        total_folders = DocumentFolder.objects.filter(is_active=True).count()
        root_folders = DocumentFolder.objects.filter(
            is_active=True,
            parent__isnull=True
        ).count()
        
        return Response({
            'total_folders': total_folders,
            'root_folders': root_folders,
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du calcul des statistiques: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
