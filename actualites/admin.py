from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'category', 'author', 'date', 'is_pinned']
    list_filter = ['type', 'category', 'is_pinned', 'date']
    search_fields = ['title', 'content', 'author']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('type', 'title', 'content', 'category', 'is_pinned')
        }),
        ('Auteur', {
            'fields': ('author', 'author_role', 'author_avatar')
        }),
        ('Dates et heures', {
            'fields': ('date', 'time')
        }),
        ('Médias', {
            'fields': ('image', 'gallery_images', 'gallery_title', 'video', 'video_poster')
        }),
        ('Contenu', {
            'fields': ('content_type',)
        }),
    )
