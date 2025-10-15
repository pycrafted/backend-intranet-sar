from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count
from django.db import models
from django.utils import timezone
import logging
from .models import Article
from .serializers import ArticleSerializer, ArticleCreateSerializer

# Configuration du logger
logger = logging.getLogger(__name__)


class ArticleListAPIView(generics.ListAPIView):
    """
    API endpoint pour récupérer la liste des articles avec filtrage et recherche
    """
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]  # Permettre l'accès sans authentification
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Article.objects.all()
        
        # Log de débogage pour les requêtes d'articles
        logger.info(f"🔍 [ARTICLES_API] Requête articles - Origin: {self.request.META.get('HTTP_ORIGIN', 'Unknown')}")
        logger.info(f"🔍 [ARTICLES_API] Headers: {dict(self.request.META)}")
        
        # Filtrage par type
        article_type = self.request.query_params.get('type', None)
        if article_type and article_type != 'all':
            queryset = queryset.filter(type=article_type)
        
        
        
        # Recherche textuelle
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Filtrage temporel
        time_filter = self.request.query_params.get('time_filter', None)
        if time_filter and time_filter != 'all':
            from datetime import timedelta, date
            now = timezone.now().date()
            if time_filter == 'today':
                queryset = queryset.filter(date=now)
            elif time_filter == 'week':
                # Cette semaine (lundi au dimanche)
                start_of_week = now - timedelta(days=now.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                queryset = queryset.filter(date__range=[start_of_week, end_of_week])
            elif time_filter == 'month':
                # Ce mois
                start_of_month = date(now.year, now.month, 1)
                if now.month == 12:
                    end_of_month = date(now.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_of_month = date(now.year, now.month + 1, 1) - timedelta(days=1)
                queryset = queryset.filter(date__range=[start_of_month, end_of_month])
        
        return queryset


class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, modifier et supprimer un article
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]  # Permettre l'accès sans authentification
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """
        Modifier un article avec logging
        """
        instance = self.get_object()
        
        try:
            serializer = ArticleCreateSerializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                response_serializer = ArticleSerializer(instance, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la modification: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprimer un article
        """
        instance = self.get_object()
        
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la suppression: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




@api_view(['POST'])
def create_article(request):
    """
    API endpoint pour créer un nouvel article (publication ou annonce)
    """
    try:
        serializer = ArticleCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            article_data = serializer.validated_data.copy()
            
            if not article_data.get('date'):
                article_data['date'] = timezone.now().date()
            if not article_data.get('time'):
                article_data['time'] = timezone.now().time()
            
            article = Article.objects.create(**article_data)
            response_serializer = ArticleSerializer(article, context={'request': request})
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': f'Erreur interne du serveur: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def article_stats(request):
    """
    API endpoint pour récupérer les statistiques des filtres
    """
    from datetime import timedelta, date
    
    # Statistiques par type
    type_stats = {}
    for type_choice in Article.TYPE_CHOICES:
        type_key = type_choice[0]
        count = Article.objects.filter(type=type_key).count()
        type_stats[type_key + 's'] = count
    
    type_stats['all'] = Article.objects.count()
    
    
    # Statistiques temporelles
    now = timezone.now().date()
    time_stats = {
        'today': Article.objects.filter(date=now).count(),
        'week': Article.objects.filter(
            date__range=[
                now - timedelta(days=now.weekday()),
                now - timedelta(days=now.weekday()) + timedelta(days=6)
            ]
        ).count(),
        'month': Article.objects.filter(
            date__range=[
                date(now.year, now.month, 1),
                date(now.year, now.month + 1, 1) - timedelta(days=1) if now.month < 12 
                else date(now.year + 1, 1, 1) - timedelta(days=1)
            ]
        ).count()
    }
    
    return Response({
        'filters': type_stats,
        'timeFilters': time_stats
    })
