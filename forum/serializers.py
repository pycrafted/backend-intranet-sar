from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Forum, Conversation, Comment, CommentLike
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserForumSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les informations utilisateur dans le forum
    """
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'avatar_url']
    
    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        return obj.username or obj.email
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                try:
                    # Essayer de construire l'URL absolue
                    return request.build_absolute_uri(obj.avatar.url)
                except Exception:
                    # Si échec (ex: testserver), retourner l'URL relative
                    return obj.avatar.url
            return obj.avatar.url
        return None


class ForumSerializer(serializers.ModelSerializer):
    """
    Serializer pour les forums (catégories)
    """
    # Utiliser source pour pointer vers les champs annotés du queryset
    # Si les champs annotés n'existent pas, utiliser les propriétés du modèle
    member_count = serializers.SerializerMethodField()
    conversation_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    # Ne pas inclure 'image' dans les fields pour éviter la sérialisation automatique par DRF
    # qui cause des erreurs avec build_absolute_uri()
    
    class Meta:
        model = Forum
        fields = [
            'id',
            'name',
            'description',
            'image_url',
            'is_active',
            'member_count',
            'conversation_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Retourne le nombre de membres - utilise le champ annoté si disponible"""
        try:
            logger.debug(f"🔵 [FORUM_SERIALIZER] get_member_count appelé pour Forum {obj.id}")
            # Vérifier si le champ annoté existe (depuis le queryset)
            if hasattr(obj, 'annotated_member_count'):
                count = obj.annotated_member_count
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Utilisation champ annoté: {count}")
                return count
            
            # Sinon utiliser la propriété du modèle
            try:
                count = obj.member_count
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Utilisation propriété modèle: {count}")
                return count
            except Exception:
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Erreur propriété, retour 0")
                return 0
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur get_member_count pour Forum {obj.id}: {e}", exc_info=True)
            return 0
    
    def get_conversation_count(self, obj):
        """Retourne le nombre de conversations - utilise le champ annoté si disponible"""
        try:
            logger.debug(f"🔵 [FORUM_SERIALIZER] get_conversation_count appelé pour Forum {obj.id}")
            # Vérifier si le champ annoté existe (depuis le queryset)
            if hasattr(obj, 'annotated_conversation_count'):
                count = obj.annotated_conversation_count
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Utilisation champ annoté: {count}")
                return count
            
            # Sinon utiliser la propriété du modèle
            try:
                count = obj.conversation_count
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Utilisation propriété modèle: {count}")
                return count
            except Exception:
                logger.debug(f"🔵 [FORUM_SERIALIZER]   - Erreur propriété, retour 0")
                return 0
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur get_conversation_count pour Forum {obj.id}: {e}", exc_info=True)
            return 0
    
    def to_representation(self, instance):
        """Override pour la sérialisation"""
        try:
            logger.info(f"🔵 [FORUM_SERIALIZER] to_representation appelé pour Forum ID={instance.id}, name='{instance.name}'")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - is_active: {instance.is_active}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - has annotated_member_count: {hasattr(instance, 'annotated_member_count')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - has annotated_conversation_count: {hasattr(instance, 'annotated_conversation_count')}")
            
            data = super().to_representation(instance)
            
            logger.info(f"🔵 [FORUM_SERIALIZER] Données sérialisées pour Forum {instance.id}:")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - id: {data.get('id')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - name: {data.get('name')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - is_active: {data.get('is_active')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - member_count: {data.get('member_count')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - conversation_count: {data.get('conversation_count')}")
            logger.info(f"🔵 [FORUM_SERIALIZER]   - image_url: {data.get('image_url')}")
            
            return data
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur dans to_representation pour Forum {instance.id}: {e}", exc_info=True)
            raise
    
    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image"""
        try:
            if not obj.image:
                return None
            
            if not hasattr(obj.image, 'url'):
                return None
            
            image_url = obj.image.url
            
            request = self.context.get('request')
            if request:
                try:
                    absolute_url = request.build_absolute_uri(image_url)
                    return absolute_url
                except Exception as e:
                    logger.warning(f"⚠️ [FORUM_SERIALIZER] Erreur build_absolute_uri: {e}")
                    # Si échec (ex: DisallowedHost, testserver), construire manuellement
                    from django.conf import settings
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    return f"{base_url}{image_url}"
            
            # Si pas de request, construire avec les settings
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{image_url}"
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur dans get_image_url pour Forum {obj.id}: {e}", exc_info=True)
            return None


class ForumCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour de forums
    """
    class Meta:
        model = Forum
        fields = ['name', 'description', 'image', 'is_active']
    
    def validate_name(self, value):
        """Valide le nom du forum"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du forum est obligatoire.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le nom du forum doit contenir au moins 3 caractères.")
        return value.strip()


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les commentaires
    """
    author = UserForumSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'conversation',
            'author',
            'author_id',
            'author_avatar',
            'content',
            'likes_count',
            'is_liked',
            'timestamp',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_likes_count(self, obj):
        """Retourne le nombre de likes - utilise le champ annoté si disponible"""
        try:
            # Vérifier si le champ annoté existe (depuis le queryset)
            if hasattr(obj, 'annotated_likes_count'):
                return obj.annotated_likes_count
            
            # Sinon utiliser la propriété du modèle
            try:
                return obj.likes_count
            except Exception:
                return 0
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur get_likes_count pour Comment {obj.id}: {e}", exc_info=True)
            return 0
    
    def get_is_liked(self, obj):
        """Vérifie si l'utilisateur connecté a liké ce commentaire"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(comment=obj, user=request.user).exists()
        return False
    
    def get_timestamp(self, obj):
        """Retourne un timestamp formaté pour le frontend"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 7:
            return obj.created_at.strftime('%d/%m/%Y')
        elif diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    
    def get_author_avatar(self, obj):
        """Retourne l'URL de l'avatar de l'auteur"""
        if obj.author.avatar and hasattr(obj.author.avatar, 'url'):
            request = self.context.get('request')
            if request:
                try:
                    # Essayer de construire l'URL absolue
                    return request.build_absolute_uri(obj.author.avatar.url)
                except Exception as e:
                    # Si échec (ex: DisallowedHost, testserver), construire manuellement
                    from django.conf import settings
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    return f"{base_url}{obj.author.avatar.url}"
            # Si pas de request, construire avec les settings
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{obj.author.avatar.url}"
        return None


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de commentaires
    """
    class Meta:
        model = Comment
        fields = ['conversation', 'content']
    
    def validate_content(self, value):
        """Valide le contenu du commentaire"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le contenu du commentaire est obligatoire.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 3 caractères.")
        return value.strip()


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer pour les conversations (posts)
    """
    author = UserForumSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    forum = ForumSerializer(read_only=True)
    forum_id = serializers.IntegerField(write_only=True)
    replies_count = serializers.SerializerMethodField()
    views = serializers.IntegerField(source='views_count', read_only=True)
    last_activity = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    # Ne pas inclure 'image' dans les fields pour éviter la sérialisation automatique par DRF
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'forum',
            'forum_id',
            'author',
            'author_id',
            'author_avatar',
            'title',
            'description',
            'content',
            'image_url',
            'is_resolved',
            'views',
            'replies_count',
            'last_activity',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        """Retourne le nombre de réponses - utilise le champ annoté si disponible"""
        try:
            # Vérifier si le champ annoté existe (depuis le queryset)
            if hasattr(obj, 'annotated_replies_count'):
                return obj.annotated_replies_count
            
            # Sinon utiliser la propriété du modèle
            try:
                return obj.replies_count
            except Exception:
                return 0
        except Exception as e:
            logger.error(f"❌ [FORUM_SERIALIZER] Erreur get_replies_count pour Conversation {obj.id}: {e}", exc_info=True)
            return 0
    
    def get_last_activity(self, obj):
        """Retourne la dernière activité formatée"""
        from django.utils import timezone
        now = timezone.now()
        
        # Utiliser la date du dernier commentaire si disponible, sinon la date de création
        last_comment = obj.comments.order_by('-created_at').first()
        if last_comment:
            diff = now - last_comment.created_at
        else:
            diff = now - obj.created_at
        
        if diff.days > 7:
            date_to_use = last_comment.created_at if last_comment else obj.created_at
            return date_to_use.strftime('%d/%m/%Y')
        elif diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    
    def get_author_avatar(self, obj):
        """Retourne l'URL de l'avatar de l'auteur"""
        if obj.author.avatar and hasattr(obj.author.avatar, 'url'):
            request = self.context.get('request')
            if request:
                try:
                    # Essayer de construire l'URL absolue
                    return request.build_absolute_uri(obj.author.avatar.url)
                except Exception as e:
                    # Si échec (ex: DisallowedHost, testserver), construire manuellement
                    from django.conf import settings
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    return f"{base_url}{obj.author.avatar.url}"
            # Si pas de request, construire avec les settings
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{obj.author.avatar.url}"
        return None
    
    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image"""
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                try:
                    # Essayer de construire l'URL absolue
                    return request.build_absolute_uri(obj.image.url)
                except Exception as e:
                    # Si échec (ex: DisallowedHost, testserver), construire manuellement
                    from django.conf import settings
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    return f"{base_url}{obj.image.url}"
            # Si pas de request, construire avec les settings
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{obj.image.url}"
        return None


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de conversations
    Supporte deux modes :
    - Mode simple : juste 'content' (génère automatiquement title et description)
    - Mode complet : 'title' et 'description' (pour compatibilité)
    """
    content = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = Conversation
        fields = ['forum', 'content', 'title', 'description', 'image']
    
    def validate(self, attrs):
        """Valide que soit content, soit title+description sont fournis"""
        content = attrs.get('content', '').strip() if attrs.get('content') else ''
        title = attrs.get('title', '').strip() if attrs.get('title') else ''
        description = attrs.get('description', '').strip() if attrs.get('description') else ''
        
        # Mode simple : content fourni
        if content:
            if len(content) < 3:
                raise serializers.ValidationError({"content": "Le contenu doit contenir au moins 3 caractères."})
            # Générer title et description depuis content
            if not title:
                if len(content) > 300:
                    attrs['title'] = content[:297] + "..."
                else:
                    attrs['title'] = content
            if not description:
                attrs['description'] = content
        # Mode complet : title et description fournis
        elif title or description:
            if not title:
                raise serializers.ValidationError({"title": "Le titre est requis si le contenu n'est pas fourni."})
            if len(title) < 3:
                raise serializers.ValidationError({"title": "Le titre doit contenir au moins 3 caractères."})
            if not description:
                attrs['description'] = title
            elif len(description) < 3:
                raise serializers.ValidationError({"description": "La description doit contenir au moins 3 caractères."})
        else:
            raise serializers.ValidationError("Vous devez fournir soit 'content', soit 'title' (et optionnellement 'description').")
        
        return attrs
    
    def create(self, validated_data):
        """Créer la conversation en gérant le contenu"""
        content = validated_data.pop('content', None)
        if content:
            # Le save() du modèle générera automatiquement title et description
            validated_data['content'] = content
        
        return super().create(validated_data)


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour de conversations (titre, description, image, is_resolved)
    """
    class Meta:
        model = Conversation
        fields = ['title', 'description', 'image', 'is_resolved']
    
    def validate_title(self, value):
        """Valide le titre de la conversation"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Le titre doit contenir au moins 5 caractères.")
        return value.strip() if value else value
    
    def validate_description(self, value):
        """Valide la description de la conversation"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("La description doit contenir au moins 10 caractères.")
        return value.strip() if value else value

