from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class UserAdmin(BaseUserAdmin):
    """Administration personnalisée pour le modèle User avec le champ matricule"""
    
    # Ajouter les champs personnalisés dans la section "Personal info"
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'matricule', 'position', 'phone_number', 'phone_fixed', 'department', 'avatar', 'manager')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Champs affichés lors de la création d'un utilisateur
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'matricule', 'position', 'phone_number', 'phone_fixed', 'department'),
        }),
    )
    
    # Champs affichés dans la liste
    list_display = ('username', 'email', 'first_name', 'last_name', 'matricule', 'position', 'department', 'phone_number', 'phone_fixed', 'is_staff', 'is_active')
    
    # Champs de recherche
    search_fields = ('username', 'email', 'first_name', 'last_name', 'matricule', 'position', 'phone_number', 'phone_fixed')
    
    # Filtres
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'department', 'position')


admin.site.register(User, UserAdmin)

