from rest_framework import serializers
from django.db import models
from django.conf import settings
import logging
from .models import Article

# Configuration du logger
logger = logging.getLogger(__name__)


class ArticleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    video_poster_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'type', 'title', 'content', 'date', 'time',
            'image', 'image_url', 'content_type',
            'video', 'video_url', 'video_poster', 'video_poster_url'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.image.url)
                logger.info(f"🖼️ [SERIALIZER] Image URL générée: {url}")
                return url
            # En cas d'absence de request, construire l'URL manuellement
            base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
            url = f"{base_url}{settings.MEDIA_URL}{obj.image.name}"
            logger.info(f"🖼️ [SERIALIZER] Image URL fallback: {url}")
            return url
        return None
    
    def get_video_url(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.video.url)
                logger.info(f"🎥 [SERIALIZER] Video URL générée: {url}")
                return url
            # En cas d'absence de request, construire l'URL manuellement
            base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
            url = f"{base_url}{settings.MEDIA_URL}{obj.video.name}"
            logger.info(f"🎥 [SERIALIZER] Video URL fallback: {url}")
            return url
        return None
    
    def get_video_poster_url(self, obj):
        if obj.video_poster:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.video_poster.url)
                logger.info(f"🎬 [SERIALIZER] Video Poster URL générée: {url}")
                return url
            # En cas d'absence de request, construire l'URL manuellement
            base_url = getattr(settings, 'BASE_URL', 'https://backend-intranet-sar-1.onrender.com')
            url = f"{base_url}{settings.MEDIA_URL}{obj.video_poster.name}"
            logger.info(f"🎬 [SERIALIZER] Video Poster URL fallback: {url}")
            return url
        return None


class ArticleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'articles (publications et annonces)
    """
    class Meta:
        model = Article
        fields = [
            'type', 'title', 'content', 'date', 'time',
            'image', 'content_type', 'video', 'video_poster'
        ]
    
    def validate(self, data):
        # Validation spécifique selon le type d'article
        article_type = data.get('type')
        
        if article_type == 'news':
            # Pour les publications, au moins un contenu est requis (titre, contenu, image ou vidéo)
            has_title = bool(data.get('title'))
            has_content = bool(data.get('content'))
            has_image = bool(data.get('image'))
            has_video = bool(data.get('video'))
            
            if not (has_title or has_content or has_image or has_video):
                raise serializers.ValidationError("Au moins un contenu est requis pour une publication (titre, contenu, image ou vidéo).")
        
        elif article_type == 'announcement':
            # Pour les annonces, au moins un contenu est requis
            has_title = bool(data.get('title'))
            has_content = bool(data.get('content'))
            has_image = bool(data.get('image'))
            has_video = bool(data.get('video'))
            
            if not (has_title or has_content or has_image or has_video):
                raise serializers.ValidationError("Au moins un contenu est requis pour une annonce (titre, contenu, image ou vidéo).")
        
        return data


