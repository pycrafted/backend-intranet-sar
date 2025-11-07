from django.contrib import admin
from .models import Direction, Agent

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'job_title', 'manager', 'main_direction']
    list_filter = ['directions', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'matricule', 'job_title']
    filter_horizontal = ['directions']
    readonly_fields = ['full_name', 'initials', 'created_at', 'updated_at']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['directions'].label = 'Directions associées'
        form.base_fields['manager'].label = 'n+1'
        
        # Trier les managers (n+1) par ordre alphabétique (prénom de A à Z)
        if 'manager' in form.base_fields:
            form.base_fields['manager'].queryset = Agent.objects.all().order_by('first_name', 'last_name')
        
        return form
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'matricule', 'avatar', 'phone_fixed', 'phone_mobile')
        }),
        ('Poste et hiérarchie', {
            'fields': ('job_title', 'manager', 'main_direction', 'directions')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
