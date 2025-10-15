from django.contrib import admin
from .models import Direction, Agent

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'job_title', 'matricule', 'email', 'is_manager', 'is_active']
    list_filter = ['is_manager', 'is_active', 'hierarchy_level', 'directions', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'matricule', 'job_title']
    filter_horizontal = ['directions']
    readonly_fields = ['full_name', 'initials', 'hierarchy_level', 'is_manager', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'matricule')
        }),
        ('Poste et hiérarchie', {
            'fields': ('job_title', 'position_title', 'manager', 'hierarchy_level', 'is_manager')
        }),
        ('Directions', {
            'fields': ('directions', 'department_name')
        }),
        ('Contact', {
            'fields': ('phone_fixed', 'phone_mobile', 'office_location')
        }),
        ('Informations complémentaires', {
            'fields': ('position', 'is_active')
        }),
        ('Photo de profil', {
            'fields': ('avatar',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
