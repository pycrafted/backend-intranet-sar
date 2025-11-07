from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    ordering = ['name']
    
    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = "Nombre d'employés"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'position_title', 'department'
    ]
    list_filter = [
        'department'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 
        'position_title'
    ]
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone_fixed', 'phone_mobile', 'avatar')
        }),
        ('Informations professionnelles', {
            'fields': ('department', 'position_title')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department')


# Personnalisation de l'interface d'administration
admin.site.site_header = "Administration SAR - Annuaire"
admin.site.site_title = "SAR Admin"
admin.site.index_title = "Gestion de l'annuaire"
