from django.contrib import admin
from .models import Forum, ForumMessage


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'message_count_display', 
                    'participant_count_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'image', 'created_by')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def message_count_display(self, obj):
        return obj.get_message_count()
    message_count_display.short_description = 'Messages'
    
    def participant_count_display(self, obj):
        return obj.get_participant_count()
    participant_count_display.short_description = 'Participants'


@admin.register(ForumMessage)
class ForumMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'forum', 'author', 'content_preview', 'is_edited', 'created_at']
    list_filter = ['is_edited', 'created_at', 'forum']
    search_fields = ['content', 'author__username', 'author__email', 'forum__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Message', {
            'fields': ('forum', 'author', 'content')
        }),
        ('Métadonnées', {
            'fields': ('is_edited', 'created_at', 'updated_at')
        }),
    )
    
    def content_preview(self, obj):
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_preview.short_description = 'Contenu'
