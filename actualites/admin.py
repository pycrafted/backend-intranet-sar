from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'date']
    list_filter = ['type', 'date']
    search_fields = ['title', 'content']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('type', 'title', 'content')
        }),
        ('Dates et heures', {
            'fields': ('date', 'time')
        }),
        ('Médias', {
            'fields': ('image', 'video', 'video_poster')
        }),
        ('Contenu', {
            'fields': ('content_type',)
        }),
    )
