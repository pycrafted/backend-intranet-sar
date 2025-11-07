from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.contrib.auth import get_user_model
from .models import Forum, Conversation, Comment, CommentLike
from .serializers import (
    ForumSerializer,
    ForumCreateUpdateSerializer,
    ConversationSerializer,
    ConversationCreateSerializer,
    ConversationUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


# ===== VUES POUR LES FORUMS =====

class ForumListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des forums
    """
    queryset = Forum.objects.filter(is_active=True).annotate(
        annotated_member_count=Count('conversations__author', distinct=True),
        annotated_conversation_count=Count('conversations', distinct=True)
    ).order_by('name')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Override pour ajouter des logs"""
        queryset = super().get_queryset()
        logger.info(f"🔵 [FORUM_VIEW] get_queryset() appelé")
        logger.info(f"🔵 [FORUM_VIEW] SQL query: {queryset.query}")
        count = queryset.count()
        logger.info(f"🔵 [FORUM_VIEW] Nombre de forums actifs trouvés: {count}")
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ForumCreateUpdateSerializer
        return ForumSerializer
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """Override list pour gérer la sérialisation"""
        try:
            logger.info("=" * 80)
            logger.info("🔵 [FORUM_VIEW] ===== DÉBUT ForumListAPIView.list =====")
            logger.info(f"🔵 [FORUM_VIEW] Méthode HTTP: {request.method}")
            logger.info(f"🔵 [FORUM_VIEW] URL: {request.build_absolute_uri()}")
            logger.info(f"🔵 [FORUM_VIEW] User: {request.user} (authenticated: {request.user.is_authenticated})")
            
            # Récupérer le queryset de base
            base_queryset = self.get_queryset()
            logger.info(f"🔵 [FORUM_VIEW] Queryset de base (avant filtre): {base_queryset.query}")
            logger.info(f"🔵 [FORUM_VIEW] Nombre de forums dans queryset de base: {base_queryset.count()}")
            
            # Lister tous les forums (même inactifs) pour debug
            all_forums = Forum.objects.all()
            logger.info(f"🔵 [FORUM_VIEW] TOTAL forums en base (tous statuts): {all_forums.count()}")
            for forum in all_forums:
                logger.info(f"🔵 [FORUM_VIEW]   - Forum ID={forum.id}, name='{forum.name}', is_active={forum.is_active}")
            
            queryset = self.filter_queryset(base_queryset)
            logger.info(f"🔵 [FORUM_VIEW] Queryset après filtre: {queryset.query}")
            logger.info(f"🔵 [FORUM_VIEW] Nombre de forums après filtre: {queryset.count()}")
            
            # Vérifier la pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                logger.info(f"🔵 [FORUM_VIEW] Pagination activée, page: {page}")
                serializer = self.get_serializer(page, many=True)
                logger.info(f"🔵 [FORUM_VIEW] Données sérialisées (page): {len(serializer.data)} forums")
                response = self.get_paginated_response(serializer.data)
                logger.info(f"🔵 [FORUM_VIEW] Réponse paginée créée")
                logger.info("=" * 80)
                return response
            
            # Sérialiser sans pagination
            logger.info(f"🔵 [FORUM_VIEW] Pas de pagination, sérialisation directe")
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"🔵 [FORUM_VIEW] Données sérialisées: {len(serializer.data)} forums")
            for idx, forum_data in enumerate(serializer.data):
                logger.info(f"🔵 [FORUM_VIEW]   Forum {idx+1}: ID={forum_data.get('id')}, name='{forum_data.get('name')}', is_active={forum_data.get('is_active')}")
            
            response_data = serializer.data
            logger.info(f"🔵 [FORUM_VIEW] Réponse finale: {len(response_data)} forums")
            logger.info("=" * 80)
            return Response(response_data)
        except Exception as e:
            logger.error(f"❌ [FORUM_VIEW] Erreur dans ForumListAPIView.list: {e}", exc_info=True)
            logger.error("=" * 80)
            raise
    
    def perform_create(self, serializer):
        """Créer un forum (seuls les admins peuvent créer)"""
        if not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les administrateurs peuvent créer des forums.")
        serializer.save()


class ForumDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer un forum
    """
    queryset = Forum.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ForumCreateUpdateSerializer
        return ForumSerializer
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        """Mettre à jour un forum (seuls les admins peuvent modifier)"""
        if not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les administrateurs peuvent modifier des forums.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un forum (seuls les admins peuvent supprimer)"""
        if not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des forums.")
        # Soft delete : désactiver au lieu de supprimer
        instance.is_active = False
        instance.save()


# ===== VUES POUR LES CONVERSATIONS =====

class ConversationListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des conversations
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Conversation.objects.select_related('author', 'forum').prefetch_related(
            Prefetch('comments', queryset=Comment.objects.select_related('author'))
        ).annotate(
            annotated_replies_count=Count('comments', distinct=True)
        )
        
        # Filtrer par forum si spécifié
        forum_id = self.request.query_params.get('forum', None)
        if forum_id:
            queryset = queryset.filter(forum_id=forum_id)
        
        # Filtrer par auteur si spécifié
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filtrer par résolu/non résolu
        is_resolved = self.request.query_params.get('is_resolved', None)
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        # Recherche par titre ou description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Ordre : plus anciennes en premier (pour que les plus récentes soient en bas dans le frontend)
        return queryset.order_by('created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def perform_create(self, serializer):
        """Créer une conversation avec l'utilisateur connecté comme auteur"""
        # Par défaut, les conversations créées depuis le frontend sont marquées comme non résolues (is_resolved=False)
        # Mais l'utilisateur veut qu'elles soient résolues (is_resolved=True) pour être affichées
        serializer.save(author=self.request.user, is_resolved=True)


class ConversationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer une conversation
    """
    queryset = Conversation.objects.select_related('author', 'forum').prefetch_related(
        Prefetch('comments', queryset=Comment.objects.select_related('author'))
    ).annotate(
        annotated_replies_count=Count('comments', distinct=True)
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ConversationUpdateSerializer
        return ConversationSerializer
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer une conversation et incrémenter le compteur de vues"""
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        """Mettre à jour une conversation (seul l'auteur ou un admin peut modifier)"""
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas la permission de modifier cette conversation.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer une conversation (seul l'auteur ou un admin peut supprimer)"""
        if instance.author != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas la permission de supprimer cette conversation.")
        instance.delete()


# ===== VUES POUR LES COMMENTAIRES =====

class CommentListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des commentaires
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation', None)
        if not conversation_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Le paramètre 'conversation' est requis.")
        
        queryset = Comment.objects.filter(conversation_id=conversation_id).select_related(
            'author', 'conversation'
        ).prefetch_related(
            'likes__user'
        ).annotate(
            annotated_likes_count=Count('likes', distinct=True)
        )
        
        return queryset.order_by('created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """Créer un commentaire avec l'utilisateur connecté comme auteur"""
        serializer.save(author=self.request.user)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer un commentaire
    """
    queryset = Comment.objects.select_related('author', 'conversation').prefetch_related(
        'likes__user'
    ).annotate(
        annotated_likes_count=Count('likes', distinct=True)
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        return CommentSerializer
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        """Mettre à jour un commentaire (seul l'auteur ou un admin peut modifier)"""
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce commentaire.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un commentaire (seul l'auteur ou un admin peut supprimer)"""
        if instance.author != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas la permission de supprimer ce commentaire.")
        instance.delete()


# ===== VUES POUR LES LIKES =====

@api_view(['POST', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def comment_like_toggle(request, comment_id):
    """
    API endpoint pour liker/unliker un commentaire
    POST : Liker un commentaire
    DELETE : Unliker un commentaire
    """
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user
    
    if request.method == 'POST':
        # Liker le commentaire
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=user
        )
        
        if created:
            return Response({
                'message': 'Commentaire liké avec succès',
                'liked': True,
                'likes_count': comment.likes.count()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Vous avez déjà liké ce commentaire',
                'liked': True,
                'likes_count': comment.likes.count()
            }, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        # Unliker le commentaire
        like = CommentLike.objects.filter(comment=comment, user=user).first()
        
        if like:
            like.delete()
            return Response({
                'message': 'Like retiré avec succès',
                'liked': False,
                'likes_count': comment.likes.count()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Vous n\'avez pas liké ce commentaire',
                'liked': False,
                'likes_count': comment.likes.count()
            }, status=status.HTTP_200_OK)
