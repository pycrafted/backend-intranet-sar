from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
import logging

from .models import Forum, ForumMessage
from .serializers import (
    ForumSerializer, ForumCreateSerializer,
    ForumMessageSerializer, ForumMessageCreateSerializer
)

logger = logging.getLogger(__name__)


class ForumListAPIView(generics.ListAPIView):
    """
    API endpoint pour récupérer la liste des forums avec filtrage et recherche
    """
    serializer_class = ForumSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Forum.objects.filter(is_active=True)
        
        # Recherche textuelle
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
            )
        
        # Tri
        sort_by = self.request.query_params.get('sort', 'recent')
        if sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'popular':
            # Trier par nombre de messages décroissant
            queryset = queryset.annotate(
                msg_count=Count('messages')
            ).order_by('-msg_count', '-created_at')
        elif sort_by == 'active':
            # Trier par dernière activité (dernier message)
            queryset = queryset.annotate(
                last_msg_date=Max('messages__created_at')
            ).order_by('-last_msg_date', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset


class ForumDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint pour récupérer les détails d'un forum
    """
    queryset = Forum.objects.filter(is_active=True)
    serializer_class = ForumSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ForumCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour créer un nouveau forum
    """
    serializer_class = ForumCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        logger.info(f"Forum créé: {serializer.instance.title} par {self.request.user.username}")


class ForumUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour modifier un forum (seul le créateur peut modifier)
    """
    queryset = Forum.objects.filter(is_active=True)
    serializer_class = ForumCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Seul le créateur peut modifier
        return Forum.objects.filter(created_by=self.request.user, is_active=True)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            response_serializer = ForumSerializer(instance, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForumDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint pour supprimer un forum (soft delete - marque is_active=False)
    """
    queryset = Forum.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Seul le créateur peut supprimer
        return Forum.objects.filter(created_by=self.request.user, is_active=True)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()
        logger.info(f"Forum désactivé: {instance.title} par {self.request.user.username}")


class ForumMessageListAPIView(generics.ListAPIView):
    """
    API endpoint pour récupérer les messages d'un forum
    """
    serializer_class = ForumMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        forum_id = self.kwargs['forum_id']
        forum = get_object_or_404(Forum, id=forum_id, is_active=True)
        return ForumMessage.objects.filter(forum=forum).order_by('created_at')


class ForumMessageCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour créer un message dans un forum
    """
    serializer_class = ForumMessageCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        forum_id = self.kwargs['forum_id']
        forum = get_object_or_404(Forum, id=forum_id, is_active=True)
        message = serializer.save(forum=forum, author=self.request.user)
        logger.info(f"Message créé dans le forum {forum.title} par {self.request.user.username}")
        
        # Retourner le message complet avec author_info
        response_serializer = ForumMessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ForumMessageUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour modifier un message (seul l'auteur peut modifier)
    """
    serializer_class = ForumMessageCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Seul l'auteur peut modifier
        return ForumMessage.objects.filter(author=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            instance.is_edited = True
            instance.save()
            response_serializer = ForumMessageSerializer(instance, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForumMessageDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint pour supprimer un message (seul l'auteur ou le créateur du forum peut supprimer)
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # L'auteur ou le créateur du forum peuvent supprimer
        return ForumMessage.objects.filter(
            Q(author=self.request.user) |
            Q(forum__created_by=self.request.user)
        )
    
    def perform_destroy(self, instance):
        instance.delete()
        logger.info(f"Message supprimé du forum {instance.forum.title} par {self.request.user.username}")
