from django.contrib import admin
from .models import Conversation, Message, Participant, MessageRead


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'name', 'created_by', 'created_at', 'last_message_at', 'is_archived', 'is_pinned']
    list_filter = ['type', 'is_archived', 'is_pinned', 'created_at']
    search_fields = ['name', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']
    # Note: filter_horizontal ne peut pas être utilisé avec un modèle ManyToMany via 'through'
    # Les participants sont gérés via le modèle Participant
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('participants', 'conversation_participants__user')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'content_preview', 'created_at', 'is_deleted', 'is_edited']
    list_filter = ['message_type', 'is_deleted', 'is_edited', 'created_at']
    search_fields = ['content', 'sender__username', 'sender__email']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Aperçu'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'conversation', 'reply_to')


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'role', 'is_active', 'unread_count', 'joined_at', 'last_read_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'conversation__name']
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation', 'user')


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['read_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'user')
