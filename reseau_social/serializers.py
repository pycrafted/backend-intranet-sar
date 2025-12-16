from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from .models import Conversation, Message, Participant, MessageRead
import xml.etree.ElementTree as ET
from xml.dom import minidom

User = get_user_model()


# ============================================================================
# SERIALIZERS JSON (REST Framework standard)
# ============================================================================

class UserNestedSerializer(serializers.Serializer):
    """Serializer imbriqué pour l'utilisateur"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.avatar.url)
                else:
                    base_url = settings.BASE_URL
                    return f"{base_url}{settings.MEDIA_URL}{obj.avatar.name}"
            except Exception as e:
                # Si le fichier n'existe pas physiquement, retourner None
                print(f"Erreur lors de l'accès à l'avatar pour user {obj.id}: {e}")
                return None
        return None


class ParticipantSerializer(serializers.ModelSerializer):
    """Serializer pour les participants d'une conversation"""
    user = UserNestedSerializer(read_only=True)
    
    class Meta:
        model = Participant
        fields = ['id', 'user', 'role', 'joined_at', 'left_at', 'is_active', 
                  'unread_count', 'last_read_at']
        read_only_fields = ['id', 'joined_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer pour les conversations - Format adapté au frontend"""
    id = serializers.SerializerMethodField()  # Convertir en string pour le frontend
    # participants est un ManyToMany avec through, donc on accède directement via obj.participants.all()
    participants = serializers.SerializerMethodField()  # Utiliser SerializerMethodField pour un contrôle total
    participant_details = ParticipantSerializer(many=True, read_only=True, source='conversation_participants')
    created_by = UserNestedSerializer(read_only=True)
    display_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()  # Format frontend
    time = serializers.SerializerMethodField()  # Format frontend
    unread_count = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()  # Format frontend
    avatar = serializers.SerializerMethodField()  # Format frontend
    online = serializers.SerializerMethodField()  # Format frontend (toujours False pour l'instant)
    name = serializers.SerializerMethodField()  # Utiliser display_name comme name
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'type', 'name', 'created_by', 'participants', 'participant_details',
            'created_at', 'updated_at', 'last_message_at', 'is_archived', 'is_pinned',
            'display_name', 'last_message', 'lastMessage', 'time', 'unread_count', 'unread',
            'avatar', 'online'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_message_at']
    
    def get_id(self, obj):
        """Convertir l'ID en string pour correspondre au frontend"""
        return str(obj.id)
    
    def get_participants(self, obj):
        """Récupérer les participants via le ManyToMany"""
        try:
            # Accéder aux participants via le manager ManyToMany (même avec through)
            participants = obj.participants.all()
            return UserNestedSerializer(participants, many=True, context=self.context).data
        except Exception as e:
            # En cas d'erreur, retourner une liste vide
            print(f"Erreur lors de la récupération des participants: {e}")
            return []
    
    def get_name(self, obj):
        """Retourner le nom d'affichage comme 'name' pour le frontend"""
        return self.get_display_name(obj)
    
    def get_display_name(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.get_display_name(request.user)
            except Exception as e:
                print(f"Erreur lors de la récupération du nom d'affichage: {e}")
                return obj.name or f"Conversation #{obj.id}"
        return obj.name or f"Conversation #{obj.id}"
    
    def get_last_message(self, obj):
        """Format détaillé pour compatibilité API"""
        try:
            last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
            if last_msg:
                return {
                    'id': last_msg.id,
                    'content': last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content,
                    'sender': UserNestedSerializer(last_msg.sender, context=self.context).data if last_msg.sender else None,
                    'created_at': last_msg.created_at.isoformat(),
                    'message_type': last_msg.message_type
                }
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier message: {e}")
        return None
    
    def get_lastMessage(self, obj):
        """Format frontend - texte simple du dernier message"""
        try:
            last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
            if last_msg:
                return last_msg.content
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier message: {e}")
        return "Aucun message"
    
    def get_time(self, obj):
        """Format frontend - heure relative du dernier message"""
        if obj.last_message_at:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            diff = now - obj.last_message_at
            
            if diff < timedelta(minutes=1):
                return "À l'instant"
            elif diff < timedelta(hours=1):
                minutes = int(diff.total_seconds() / 60)
                return f"il y a {minutes} min"
            elif diff < timedelta(days=1):
                hours = int(diff.total_seconds() / 3600)
                return f"il y a {hours}h"
            elif diff < timedelta(days=2):
                return "Hier"
            elif diff < timedelta(days=7):
                days = diff.days
                return f"il y a {days}j"
            else:
                return obj.last_message_at.strftime("%d/%m/%Y")
        return ""
    
    def get_unread_count(self, obj):
        """Format API détaillé"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participant = obj.conversation_participants.filter(user=request.user, is_active=True).first()
                if participant:
                    return participant.unread_count
                return 0
            except Exception as e:
                # En cas d'erreur, retourner 0
                print(f"Erreur lors de la récupération du nombre de messages non lus: {e}")
                return 0
        return 0
    
    def get_unread(self, obj):
        """Format frontend - nombre de messages non lus"""
        return self.get_unread_count(obj)
    
    def get_avatar(self, obj):
        """Avatar de l'autre participant (pour conversations directes) ou du groupe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                # Pour les conversations directes, retourner l'avatar de l'autre participant
                if obj.type == 'direct':
                    other_participants = obj.participants.exclude(id=request.user.id)
                    if other_participants.exists():
                        other = other_participants.first()
                        if other and other.avatar:
                            try:
                                if request:
                                    return request.build_absolute_uri(other.avatar.url)
                                else:
                                    base_url = settings.BASE_URL
                                    return f"{base_url}{settings.MEDIA_URL}{other.avatar.name}"
                            except Exception as e:
                                print(f"Erreur lors de la construction de l'URL de l'avatar: {e}")
                                return None
            except Exception as e:
                # En cas d'erreur, retourner None
                print(f"Erreur lors de la récupération de l'avatar: {e}")
                return None
        return None
    
    def get_online(self, obj):
        """Détermine si l'autre participant (pour conversations directes) est en ligne"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        try:
            # Pour les conversations directes, vérifier le statut de l'autre participant
            if obj.type == 'direct':
                other_participants = obj.participants.exclude(id=request.user.id)
                if other_participants.exists():
                    other_user = other_participants.first()
                    return self._is_user_online(other_user)
            
            # Pour les groupes, on pourrait retourner False ou implémenter une logique différente
            return False
        except Exception as e:
            print(f"Erreur lors de la vérification du statut en ligne: {e}")
            return False
    
    def _is_user_online(self, user):
        """Vérifie si un utilisateur a une session active récente"""
        try:
            # Récupérer les sessions actives non expirées (limiter à 1000 pour performance)
            now = timezone.now()
            active_sessions = Session.objects.filter(
                expire_date__gt=now
            )[:1000]  # Limiter pour éviter de charger trop de sessions
            
            # Parcourir les sessions pour trouver celle de l'utilisateur
            for session in active_sessions:
                try:
                    session_data = session.get_decoded()
                    # Django stocke l'ID utilisateur dans '_auth_user_id' dans la session
                    user_id = session_data.get('_auth_user_id')
                    if user_id and str(user_id) == str(user.id):
                        # Une session active non expirée signifie que l'utilisateur est en ligne
                        return True
                except Exception:
                    # Ignorer les sessions corrompues
                    continue
            
            return False
        except Exception as e:
            print(f"Erreur lors de la vérification de la session pour l'utilisateur {user.id}: {e}")
            return False


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une conversation"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text='Liste des IDs des participants'
    )
    
    class Meta:
        model = Conversation
        fields = ['type', 'name', 'participant_ids']
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        request = self.context.get('request')
        
        conversation = Conversation.objects.create(
            created_by=request.user if request and request.user.is_authenticated else None,
            **validated_data
        )
        
        # Ajouter le créateur comme participant
        if request and request.user.is_authenticated:
            participant_ids.append(request.user.id)
        
        # Ajouter les participants
        participants = User.objects.filter(id__in=set(participant_ids))
        for user in participants:
            Participant.objects.create(
                conversation=conversation,
                user=user,
                is_active=True
            )
        
        return conversation


class MessageReplySerializer(serializers.Serializer):
    """Serializer pour les messages de réponse (lecture seule)"""
    id = serializers.IntegerField(read_only=True)
    content = serializers.CharField(read_only=True)
    sender = UserNestedSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class MessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages - Format adapté au frontend"""
    id = serializers.SerializerMethodField()  # Convertir en string pour le frontend
    sender = UserNestedSerializer(read_only=True)
    reply_to = MessageReplySerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()  # Format frontend
    time = serializers.SerializerMethodField()  # Format frontend
    sent = serializers.SerializerMethodField()  # Format frontend
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'text', 'message_type',
            'attachment', 'attachment_url', 'reply_to', 'created_at', 'updated_at',
            'is_edited', 'is_deleted', 'is_read', 'time', 'sent'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_edited']
    
    def get_id(self, obj):
        """Convertir l'ID en string pour correspondre au frontend"""
        return str(obj.id)
    
    def get_text(self, obj):
        """Format frontend - contenu du message"""
        # Si le message est supprimé, afficher "Message supprimé"
        if obj.is_deleted:
            return "Message supprimé"
        return obj.content
    
    def get_time(self, obj):
        """Format frontend - heure du message"""
        return obj.created_at.strftime("%H:%M")
    
    def get_sent(self, obj):
        """Format frontend - indique si le message est envoyé par l'utilisateur actuel"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user if obj.sender else False
        return False
    
    def get_attachment_url(self, obj):
        # Ne pas retourner l'URL de la pièce jointe si le message est supprimé
        if obj.is_deleted:
            return None
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            else:
                base_url = settings.BASE_URL
                return f"{base_url}{settings.MEDIA_URL}{obj.attachment.name}"
        return None
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return MessageRead.objects.filter(message=obj, user=request.user).exists()
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un message"""
    content = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Message
        fields = ['conversation', 'content', 'message_type', 'attachment', 'reply_to']
    
    def validate(self, attrs):
        """Valider qu'il y a au moins du contenu ou un fichier"""
        content = attrs.get('content', '')
        attachment = attrs.get('attachment')
        
        # Pour FormData, le fichier peut être dans request.data (via MultiPartParser)
        # ou dans request.FILES directement
        if not attachment:
            request = self.context.get('request')
            if request:
                # Essayer request.data d'abord (DRF combine POST et FILES)
                if hasattr(request, 'data') and request.data.get('attachment'):
                    attachment = request.data.get('attachment')
                # Sinon essayer request.FILES
                elif hasattr(request, 'FILES') and request.FILES.get('attachment'):
                    attachment = request.FILES.get('attachment')
        
        if not content.strip() and not attachment:
            raise serializers.ValidationError("Le message doit contenir du texte ou une pièce jointe")
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Utilisateur non authentifié")
        
        # Si le contenu est vide, mettre une chaîne vide ou un message par défaut
        if not validated_data.get('content'):
            validated_data['content'] = ''
        
        message = Message.objects.create(
            sender=request.user,
            **validated_data
        )
        
        # Mettre à jour la date du dernier message de la conversation
        conversation = message.conversation
        conversation.update_last_message_at()
        
        # Les compteurs de messages non lus seront mis à jour dans la vue
        
        return message


# ============================================================================
# SERIALIZERS XML (Protocole de communication XML)
# ============================================================================

class XMLSerializer:
    """
    Classe utilitaire pour convertir les données en format XML
    Utilisé pour le protocole de communication XML
    """
    
    @staticmethod
    def prettify_xml(element):
        """Formate le XML de manière lisible"""
        rough_string = ET.tostring(element, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    @staticmethod
    def serialize_message(message, request=None):
        """Sérialise un message en XML"""
        msg_elem = ET.Element('message')
        msg_elem.set('id', str(message.id))
        msg_elem.set('conversation_id', str(message.conversation.id))
        msg_elem.set('type', message.message_type)
        
        # Sender
        sender_elem = ET.SubElement(msg_elem, 'sender')
        if message.sender:
            sender_elem.set('id', str(message.sender.id))
            sender_elem.set('username', message.sender.username)
            sender_elem.set('email', message.sender.email or '')
            full_name = message.sender.get_full_name() or message.sender.username
            sender_elem.set('full_name', full_name)
            
            # Avatar URL
            if message.sender.avatar:
                if request:
                    avatar_url = request.build_absolute_uri(message.sender.avatar.url)
                else:
                    base_url = settings.BASE_URL
                    avatar_url = f"{base_url}{settings.MEDIA_URL}{message.sender.avatar.name}"
                sender_elem.set('avatar_url', avatar_url)
        else:
            sender_elem.set('type', 'system')
        
        # Content
        content_elem = ET.SubElement(msg_elem, 'content')
        content_elem.text = message.content
        
        # Timestamps
        timestamps_elem = ET.SubElement(msg_elem, 'timestamps')
        ET.SubElement(timestamps_elem, 'created_at').text = message.created_at.isoformat()
        ET.SubElement(timestamps_elem, 'updated_at').text = message.updated_at.isoformat()
        
        # Metadata
        metadata_elem = ET.SubElement(msg_elem, 'metadata')
        metadata_elem.set('is_edited', str(message.is_edited).lower())
        metadata_elem.set('is_deleted', str(message.is_deleted).lower())
        
        # Attachment
        if message.attachment:
            attachment_elem = ET.SubElement(msg_elem, 'attachment')
            if request:
                attachment_url = request.build_absolute_uri(message.attachment.url)
            else:
                base_url = settings.BASE_URL
                attachment_url = f"{base_url}{settings.MEDIA_URL}{message.attachment.name}"
            attachment_elem.set('url', attachment_url)
            attachment_elem.set('name', message.attachment.name)
        
        # Reply to
        if message.reply_to:
            reply_elem = ET.SubElement(msg_elem, 'reply_to')
            reply_elem.set('id', str(message.reply_to.id))
            reply_elem.text = message.reply_to.content[:100]
        
        return msg_elem
    
    @staticmethod
    def serialize_conversation(conversation, request=None):
        """Sérialise une conversation en XML"""
        conv_elem = ET.Element('conversation')
        conv_elem.set('id', str(conversation.id))
        conv_elem.set('type', conversation.type)
        
        if conversation.name:
            conv_elem.set('name', conversation.name)
        
        # Creator
        if conversation.created_by:
            creator_elem = ET.SubElement(conv_elem, 'created_by')
            creator_elem.set('id', str(conversation.created_by.id))
            creator_elem.set('username', conversation.created_by.username)
        
        # Display name
        if request and request.user.is_authenticated:
            display_name = conversation.get_display_name(request.user)
            conv_elem.set('display_name', display_name)
        
        # Participants
        participants_elem = ET.SubElement(conv_elem, 'participants')
        for participant in conversation.conversation_participants.filter(is_active=True):
            participant_elem = ET.SubElement(participants_elem, 'participant')
            participant_elem.set('id', str(participant.user.id))
            participant_elem.set('username', participant.user.username)
            participant_elem.set('role', participant.role)
            participant_elem.set('unread_count', str(participant.unread_count))
        
        # Timestamps
        timestamps_elem = ET.SubElement(conv_elem, 'timestamps')
        ET.SubElement(timestamps_elem, 'created_at').text = conversation.created_at.isoformat()
        ET.SubElement(timestamps_elem, 'updated_at').text = conversation.updated_at.isoformat()
        if conversation.last_message_at:
            ET.SubElement(timestamps_elem, 'last_message_at').text = conversation.last_message_at.isoformat()
        
        # Metadata
        metadata_elem = ET.SubElement(conv_elem, 'metadata')
        metadata_elem.set('is_archived', str(conversation.is_archived).lower())
        metadata_elem.set('is_pinned', str(conversation.is_pinned).lower())
        
        # Last message
        last_message = conversation.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_message:
            last_msg_elem = ET.SubElement(conv_elem, 'last_message')
            last_msg_elem.set('id', str(last_message.id))
            last_msg_elem.set('preview', last_message.content[:100])
            last_msg_elem.set('created_at', last_message.created_at.isoformat())
        
        return conv_elem
    
    @staticmethod
    def create_messages_xml(messages, request=None):
        """Crée un document XML pour une liste de messages"""
        root = ET.Element('messages')
        root.set('count', str(len(messages)))
        
        for message in messages:
            msg_elem = XMLSerializer.serialize_message(message, request)
            root.append(msg_elem)
        
        return root
    
    @staticmethod
    def create_conversations_xml(conversations, request=None):
        """Crée un document XML pour une liste de conversations"""
        root = ET.Element('conversations')
        root.set('count', str(len(conversations)))
        
        for conversation in conversations:
            conv_elem = XMLSerializer.serialize_conversation(conversation, request)
            root.append(conv_elem)
        
        return root


def parse_xml_message(xml_string):
    """
    Parse un message XML et retourne un dictionnaire
    Utilisé pour recevoir des messages au format XML
    """
    try:
        root = ET.fromstring(xml_string)
        
        if root.tag != 'message':
            raise ValueError("L'élément racine doit être 'message'")
        
        data = {
            'conversation_id': root.get('conversation_id'),
            'content': root.findtext('content', ''),
            'message_type': root.get('type', 'text'),
        }
        
        # Attachment
        attachment_elem = root.find('attachment')
        if attachment_elem is not None:
            data['attachment_url'] = attachment_elem.get('url')
        
        # Reply to
        reply_elem = root.find('reply_to')
        if reply_elem is not None:
            data['reply_to_id'] = reply_elem.get('id')
        
        return data
    except ET.ParseError as e:
        raise ValueError(f"Erreur de parsing XML: {str(e)}")

