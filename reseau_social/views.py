from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.db.models import Q, Count, Max, F
from django.db import models
from django.utils import timezone
from django.http import HttpResponse
import xml.etree.ElementTree as ET
from xml.dom import minidom

from django.contrib.auth import get_user_model
from .models import Conversation, Message, Participant, MessageRead
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageCreateSerializer,
    ParticipantSerializer, XMLSerializer, parse_xml_message
)

User = get_user_model()


class ConversationListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des conversations
    Supporte JSON et XML
    GET /api/reseau-social/conversations/ - Liste des conversations de l'utilisateur
    POST /api/reseau-social/conversations/ - Créer une nouvelle conversation
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def get_queryset(self):
        """Retourne les conversations où l'utilisateur est participant actif, triées par favoris puis date"""
        user = self.request.user
        return Conversation.objects.filter(
            conversation_participants__user=user,
            conversation_participants__is_active=True
        ).distinct().select_related(
            'created_by'  # created_by est une ForeignKey, mais avatar (ImageField) n'est pas une relation
        ).prefetch_related(
            # Pour ManyToMany avec 'through', on utilise conversation_participants
            'conversation_participants',  # Précharger les objets Participant
            'conversation_participants__user',  # Précharger les users des participants
            # Note: conversation_participants__user__avatar ne fonctionne pas car avatar est un ImageField, pas une relation
            # Les ImageField sont chargés automatiquement avec l'objet User
            'participants',  # Précharger les participants via ManyToMany (nécessaire pour obj.participants.all())
            'messages',  # Précharger les messages pour last_message
            'messages__sender'  # Précharger les senders des messages (avatar chargé avec User)
        ).order_by('-is_pinned', '-last_message_at', '-created_at')  # Favoris en premier, puis par date
    
    def list(self, request, *args, **kwargs):
        """Liste les conversations avec support XML"""
        try:
            format_type = request.GET.get('format', 'json').lower()
            queryset = self.filter_queryset(self.get_queryset())
            
            if format_type == 'xml':
                # Retourner en XML
                conversations = list(queryset)
                xml_root = XMLSerializer.create_conversations_xml(conversations, request)
                xml_str = ET.tostring(xml_root, encoding='utf-8').decode('utf-8')
                return HttpResponse(
                    f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                    content_type='application/xml'
                )
            else:
                # Retourner en JSON (par défaut)
                serializer = self.get_serializer(queryset, many=True, context={'request': request})
                return Response(serializer.data)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ [CONVERSATION_LIST] Erreur lors de la récupération des conversations: {e}")
            print(f"Détails: {error_details}")
            return Response(
                {'error': 'Erreur lors de la récupération des conversations', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """Créer une conversation avec support XML"""
        format_type = request.GET.get('format', 'json').lower()
        
        # Vérifier si le contenu est XML
        if request.content_type == 'application/xml' or format_type == 'xml':
            try:
                xml_data = request.body.decode('utf-8')
                # Parser le XML (à implémenter selon votre format)
                # Pour l'instant, on utilise le serializer JSON
                serializer = self.get_serializer(data=request.data)
            except Exception as e:
                return Response(
                    {'error': f'Erreur de parsing XML: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            conversation = serializer.save()
            
            if format_type == 'xml':
                # Retourner en XML
                xml_elem = XMLSerializer.serialize_conversation(conversation, request)
                xml_str = ET.tostring(xml_elem, encoding='utf-8').decode('utf-8')
                return HttpResponse(
                    f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                    content_type='application/xml',
                    status=status.HTTP_201_CREATED
                )
            else:
                # Retourner en JSON
                response_serializer = ConversationSerializer(conversation, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour et supprimer une conversation
    GET /api/reseau-social/conversations/<id>/ - Détails d'une conversation
    PUT/PATCH /api/reseau-social/conversations/<id>/ - Mettre à jour
    DELETE /api/reseau-social/conversations/<id>/ - Supprimer (archiver)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            conversation_participants__user=user,
            conversation_participants__is_active=True
        ).distinct()
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer une conversation avec support XML"""
        format_type = request.GET.get('format', 'json').lower()
        instance = self.get_object()
        
        if format_type == 'xml':
            xml_elem = XMLSerializer.serialize_conversation(instance, request)
            xml_str = ET.tostring(xml_elem, encoding='utf-8').decode('utf-8')
            return HttpResponse(
                f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                content_type='application/xml'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Supprimer une conversation pour l'utilisateur actuel uniquement (comme WhatsApp)
        Désactive le participant au lieu d'archiver la conversation globalement"""
        instance = self.get_object()
        user = request.user
        
        # Trouver le participant de l'utilisateur actuel
        try:
            participant = Participant.objects.get(
                conversation=instance,
                user=user,
                is_active=True
            )
            # Désactiver le participant (suppression locale, pas globale)
            participant.is_active = False
            participant.left_at = timezone.now()
            participant.save(update_fields=['is_active', 'left_at'])
            
            return Response(
                {'message': 'Conversation supprimée avec succès'},
                status=status.HTTP_200_OK
            )
        except Participant.DoesNotExist:
            return Response(
                {'error': 'Vous n\'êtes pas participant de cette conversation'},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des messages dans une conversation
    GET /api/reseau-social/conversations/<conversation_id>/messages/ - Liste des messages
    POST /api/reseau-social/conversations/<conversation_id>/messages/ - Créer un message
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support FormData et JSON
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Retourne les messages d'une conversation"""
        conversation_id = self.kwargs['conversation_id']
        user = self.request.user
        
        # Vérifier que l'utilisateur est participant (actif ou inactif)
        try:
            participant = Participant.objects.get(
                conversation_id=conversation_id,
                user=user
            )
        except Participant.DoesNotExist:
            return Message.objects.none()
        
        # Si le participant n'est pas actif, ne pas retourner de messages
        # (mais normalement, il devrait être réactivé automatiquement quand un message est envoyé)
        if not participant.is_active:
            return Message.objects.none()
        
        # Retourner les messages de la conversation
        queryset = Message.objects.filter(
            conversation_id=conversation_id
        ).select_related('sender', 'reply_to', 'conversation')
        
        # Si le participant a un left_at (a supprimé puis été réactivé),
        # ne montrer que les messages créés APRÈS left_at (les nouveaux messages)
        if participant.left_at:
            queryset = queryset.filter(created_at__gt=participant.left_at)
        # Sinon, montrer tous les messages (utilisateur n'a jamais supprimé)
        
        return queryset.order_by('created_at')
    
    def list(self, request, *args, **kwargs):
        """Liste les messages avec support XML"""
        format_type = request.GET.get('format', 'json').lower()
        queryset = self.filter_queryset(self.get_queryset())
        
        # Pagination
        page_size = int(request.GET.get('page_size', 50))
        offset = int(request.GET.get('offset', 0))
        
        total = queryset.count()
        messages = list(queryset[offset:offset + page_size])
        
        if format_type == 'xml':
            # Retourner en XML
            xml_root = XMLSerializer.create_messages_xml(messages, request)
            xml_root.set('total', str(total))
            xml_root.set('offset', str(offset))
            xml_root.set('page_size', str(page_size))
            xml_str = ET.tostring(xml_root, encoding='utf-8').decode('utf-8')
            return HttpResponse(
                f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                content_type='application/xml'
            )
        else:
            # Retourner en JSON
            serializer = self.get_serializer(messages, many=True)
            return Response({
                'count': total,
                'offset': offset,
                'page_size': page_size,
                'results': serializer.data
            })
    
    def create(self, request, *args, **kwargs):
        """Créer un message avec support XML et FormData"""
        format_type = request.GET.get('format', 'json').lower()
        conversation_id = self.kwargs['conversation_id']
        
        # Vérifier que l'utilisateur est participant (actif ou inactif)
        try:
            participant = Participant.objects.get(
                conversation_id=conversation_id,
                user=request.user
            )
            # Si le participant est inactif, le réactiver automatiquement
            if not participant.is_active:
                participant.is_active = True
                # Ne pas réinitialiser left_at pour garder l'historique de suppression
                participant.save(update_fields=['is_active'])
        except Participant.DoesNotExist:
            return Response(
                {'error': 'Vous n\'êtes pas participant de cette conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier si le contenu est XML
        if request.content_type == 'application/xml' or format_type == 'xml':
            try:
                xml_data = request.body.decode('utf-8')
                parsed_data = parse_xml_message(xml_data)
                parsed_data['conversation'] = conversation_id
                serializer = self.get_serializer(data=parsed_data)
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # JSON standard ou FormData (multipart/form-data)
            # Pour FormData avec MultiPartParser, les fichiers sont dans request.FILES
            # et les champs texte dans request.data
            
            # Créer un nouveau dict pour éviter les problèmes de pickle avec .copy()
            # Extraire les données texte de request.data
            data = {}
            
            # Copier les champs texte de request.data
            for key, value in request.data.items():
                # Ignorer les fichiers, ils seront dans request.FILES
                if not hasattr(value, 'read'):  # Les fichiers ont une méthode read()
                    if isinstance(value, list) and len(value) > 0:
                        data[key] = value[0] if len(value) == 1 else value
                    else:
                        data[key] = value
            
            # Ajouter les fichiers de request.FILES si présents
            if request.FILES:
                for key, file in request.FILES.items():
                    data[key] = file
            
            data['conversation'] = conversation_id
            
            # Le serializer reçoit directement data qui contient les fichiers
            serializer = self.get_serializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            message = serializer.save()
            
            # Réactiver automatiquement les participants inactifs (qui ont supprimé la conversation)
            # et mettre à jour les compteurs de messages non lus
            conversation = message.conversation
            
            # Récupérer les IDs des participants inactifs avant réactivation
            inactive_participant_ids = list(
                conversation.conversation_participants.exclude(
                    user=request.user
                ).filter(is_active=False).values_list('id', flat=True)
            )
            
            # Réactiver les participants inactifs (garder left_at pour filtrer les anciens messages)
            if inactive_participant_ids:
                Participant.objects.filter(id__in=inactive_participant_ids).update(
                    is_active=True,
                    unread_count=F('unread_count') + 1
                )
            
            # Mettre à jour les compteurs pour les participants actifs (qui n'étaient pas inactifs)
            conversation.conversation_participants.exclude(
                user=request.user
            ).filter(is_active=True).exclude(
                id__in=inactive_participant_ids
            ).update(unread_count=F('unread_count') + 1)
            
            if format_type == 'xml':
                # Retourner en XML
                xml_elem = XMLSerializer.serialize_message(message, request)
                xml_str = ET.tostring(xml_elem, encoding='utf-8').decode('utf-8')
                return HttpResponse(
                    f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                    content_type='application/xml',
                    status=status.HTTP_201_CREATED
                )
            else:
                # Retourner en JSON
                response_serializer = MessageSerializer(message, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour et supprimer un message
    GET /api/reseau-social/messages/<id>/ - Détails d'un message
    PUT/PATCH /api/reseau-social/messages/<id>/ - Mettre à jour
    DELETE /api/reseau-social/messages/<id>/ - Supprimer (soft delete)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        """Retourne les messages accessibles par l'utilisateur"""
        user = self.request.user
        return Message.objects.filter(
            conversation__conversation_participants__user=user,
            conversation__conversation_participants__is_active=True
        ).select_related('sender', 'conversation')
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer un message avec support XML"""
        format_type = request.GET.get('format', 'json').lower()
        instance = self.get_object()
        
        if format_type == 'xml':
            xml_elem = XMLSerializer.serialize_message(instance, request)
            xml_str = ET.tostring(xml_elem, encoding='utf-8').decode('utf-8')
            return HttpResponse(
                f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
                content_type='application/xml'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Mettre à jour un message (seul le créateur peut modifier)"""
        instance = self.get_object()
        
        if instance.sender != request.user:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(is_edited=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Suppression douce d'un message"""
        instance = self.get_object()
        
        if instance.sender != request.user:
            return Response(
                {'error': 'Vous ne pouvez supprimer que vos propres messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkMessagesReadView(APIView):
    """
    Vue pour marquer des messages comme lus
    POST /api/reseau-social/conversations/<conversation_id>/mark-read/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id):
        """Marquer tous les messages d'une conversation comme lus"""
        try:
            participant = Participant.objects.get(
                conversation_id=conversation_id,
                user=request.user,
                is_active=True
            )
        except Participant.DoesNotExist:
            return Response(
                {'error': 'Vous n\'êtes pas participant de cette conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les IDs des messages à marquer comme lus
        message_ids = request.data.get('message_ids', [])
        
        if not message_ids:
            # Marquer tous les messages non lus comme lus
            unread_messages = Message.objects.filter(
                conversation_id=conversation_id,
                is_deleted=False
            ).exclude(
                read_by_users__user=request.user
            )
            
            for message in unread_messages:
                MessageRead.objects.get_or_create(message=message, user=request.user)
        else:
            # Marquer des messages spécifiques
            messages = Message.objects.filter(
                id__in=message_ids,
                conversation_id=conversation_id,
                is_deleted=False
            )
            
            for message in messages:
                MessageRead.objects.get_or_create(message=message, user=request.user)
        
        # Recalculer le compteur de messages non lus en comptant réellement les messages non lus
        # au lieu de simplement mettre à 0, pour éviter les désynchronisations
        unread_count = Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False
        ).exclude(
            sender=request.user  # Exclure les messages envoyés par l'utilisateur
        ).exclude(
            read_by_users__user=request.user  # Exclure les messages déjà lus
        ).count()
        
        participant.unread_count = unread_count
        participant.last_read_at = timezone.now()
        participant.save(update_fields=['unread_count', 'last_read_at'])
        
        return Response({'message': 'Messages marqués comme lus'}, status=status.HTTP_200_OK)


class ConversationParticipantsView(generics.ListCreateAPIView):
    """
    Vue pour gérer les participants d'une conversation
    GET /api/reseau-social/conversations/<conversation_id>/participants/ - Liste
    POST /api/reseau-social/conversations/<conversation_id>/participants/ - Ajouter
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ParticipantSerializer
    
    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Participant.objects.filter(
            conversation_id=conversation_id,
            is_active=True
        ).select_related('user')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_search(request):
    """
    Endpoint pour rechercher des utilisateurs (pour créer une conversation)
    Recherche par : nom, prénom, téléphone, matricule, email, username
    GET /api/reseau-social/users/search/?q=<query>
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response(
            {'error': 'La recherche doit contenir au moins 2 caractères'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from authentication.serializers import UserSerializer
    
    # Recherche dans tous les champs pertinents
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(phone_fixed__icontains=query) |
        Q(matricule__icontains=query),
        is_active=True
    ).exclude(id=request.user.id).select_related('department').order_by('last_name', 'first_name')[:20]
    
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation_with_user(request):
    """
    Créer facilement une conversation avec un utilisateur spécifique
    POST /api/reseau-social/conversations/create-with-user/
    Body: { "user_id": <id> }
    
    Si une conversation directe existe déjà, la retourne au lieu d'en créer une nouvelle
    """
    user_id = request.data.get('user_id')
    
    if not user_id:
        return Response(
            {'error': 'user_id est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        target_user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if target_user.id == request.user.id:
        return Response(
            {'error': 'Vous ne pouvez pas créer une conversation avec vous-même'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier si une conversation directe existe déjà entre ces deux utilisateurs
    # (même si l'un des participants est inactif - pour réactiver au lieu de créer une nouvelle)
    existing_conversation = Conversation.objects.filter(
        type='direct',
        conversation_participants__user=request.user
    ).filter(
        conversation_participants__user=target_user
    ).distinct().first()
    
    if existing_conversation:
        # Réactiver les participants inactifs s'ils existent
        user_participant = Participant.objects.filter(
            conversation=existing_conversation,
            user=request.user
        ).first()
        target_participant = Participant.objects.filter(
            conversation=existing_conversation,
            user=target_user
        ).first()
        
        # Réactiver le participant de l'utilisateur actuel s'il est inactif
        if user_participant and not user_participant.is_active:
            user_participant.is_active = True
            # Ne pas réinitialiser left_at pour garder l'historique de suppression
            user_participant.save(update_fields=['is_active'])
        
        # Réactiver le participant de l'utilisateur cible s'il est inactif
        if target_participant and not target_participant.is_active:
            target_participant.is_active = True
            # Ne pas réinitialiser left_at pour garder l'historique de suppression
            target_participant.save(update_fields=['is_active'])
        
        # Retourner la conversation existante (réactivée si nécessaire)
        serializer = ConversationSerializer(existing_conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Créer une nouvelle conversation directe
    conversation = Conversation.objects.create(
        type='direct',
        created_by=request.user
    )
    
    # Ajouter les deux participants
    Participant.objects.create(
        conversation=conversation,
        user=request.user,
        is_active=True
    )
    Participant.objects.create(
        conversation=conversation,
        user=target_user,
        is_active=True
    )
    
    serializer = ConversationSerializer(conversation, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)
