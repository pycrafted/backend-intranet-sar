from django.contrib import admin
from .models import Forum, Conversation, Comment, CommentLike


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    """
    Administration des forums
    """
    list_display = ['name', 'is_active', 'member_count', 'conversation_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['member_count', 'conversation_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'image', 'is_active')
        }),
        ('Statistiques', {
            'fields': ('member_count', 'conversation_count'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        """Affiche le nombre de membres"""
        return obj.member_count
    member_count.short_description = 'Membres'
    
    def conversation_count(self, obj):
        """Affiche le nombre de conversations"""
        return obj.conversation_count
    conversation_count.short_description = 'Conversations'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Administration des conversations
    """
    list_display = ['message_preview', 'forum', 'author', 'replies_count', 'views_count', 'created_at']
    list_filter = ['forum', 'created_at']
    search_fields = ['message', 'content', 'author__email', 'author__first_name', 'author__last_name']
    readonly_fields = ['replies_count', 'views_count', 'created_at', 'updated_at']
    raw_id_fields = ['author', 'forum']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('forum', 'author', 'message')
        }),
        ('Statistiques', {
            'fields': ('replies_count', 'views_count'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }        ),
    )
    
    def message_preview(self, obj):
        """Affiche un aperçu du message"""
        if obj.message:
            return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
        elif obj.content:
            return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return "Sans message"
    message_preview.short_description = 'Message'
    
    def replies_count(self, obj):
        """Affiche le nombre de réponses"""
        return obj.replies_count
    replies_count.short_description = 'Réponses'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Administration des commentaires
    """
    list_display = ['id', 'conversation', 'author', 'content_preview', 'likes_count', 'created_at']
    list_filter = ['created_at', 'conversation__forum']
    search_fields = ['content', 'author__email', 'author__first_name', 'author__last_name', 'conversation__title']
    readonly_fields = ['likes_count', 'created_at', 'updated_at']
    raw_id_fields = ['author', 'conversation']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('conversation', 'author', 'content')
        }),
        ('Statistiques', {
            'fields': ('likes_count',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Affiche un aperçu du contenu"""
        if len(obj.content) > 100:
            return f"{obj.content[:100]}..."
        return obj.content
    content_preview.short_description = 'Contenu'
    
    def likes_count(self, obj):
        """Affiche le nombre de likes"""
        return obj.likes_count
    likes_count.short_description = 'Likes'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """
    Administration des likes de commentaires
    """
    list_display = ['id', 'comment', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment__content', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']
    raw_id_fields = ['comment', 'user']

