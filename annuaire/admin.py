from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Department, Position, Employee, OrganizationalChart


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'location']
    ordering = ['name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'level', 'is_management', 'employee_count']
    list_filter = ['department', 'level', 'is_management']
    search_fields = ['title', 'description']
    ordering = ['level', 'title']
    
    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = "Nombre d'employés"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'employee_id', 'position', 'manager_link', 
        'hierarchy_level', 'is_active', 'hire_date'
    ]
    list_filter = [
        'position__department', 'position__level', 'is_active', 
        'hire_date', 'work_schedule'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'employee_id', 
        'position__title', 'office_location'
    ]
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        ('Informations professionnelles', {
            'fields': ('employee_id', 'position', 'manager', 'hire_date', 'is_active')
        }),
        ('Localisation et horaires', {
            'fields': ('office_location', 'work_schedule'),
            'classes': ('collapse',)
        }),
        ('Compte utilisateur', {
            'fields': ('user_account',),
            'classes': ('collapse',)
        }),
    )
    
    def manager_link(self, obj):
        if obj.manager:
            url = reverse('admin:annuaire_employee_change', args=[obj.manager.id])
            return format_html('<a href="{}">{}</a>', url, obj.manager.full_name)
        return "-"
    manager_link.short_description = "Supérieur hiérarchique"
    manager_link.admin_order_field = 'manager__last_name'
    
    def hierarchy_level(self, obj):
        return obj.hierarchy_level
    hierarchy_level.short_description = "Niveau"
    hierarchy_level.admin_order_field = 'position__level'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('position', 'manager', 'position__department')
    
    # Filtre pour les managers
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manager":
            # Exclure l'employé actuel de la liste des managers possibles
            if request.resolver_match and 'object_id' in request.resolver_match.kwargs:
                current_employee_id = request.resolver_match.kwargs['object_id']
                kwargs["queryset"] = Employee.objects.exclude(id=current_employee_id)
            else:
                kwargs["queryset"] = Employee.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(OrganizationalChart)
class OrganizationalChartAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


# Personnalisation de l'interface d'administration
admin.site.site_header = "Administration SAR - Annuaire & Organigramme"
admin.site.site_title = "SAR Admin"
admin.site.index_title = "Gestion de l'annuaire et de l'organigramme"
