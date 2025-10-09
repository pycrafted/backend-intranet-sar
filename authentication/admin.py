from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Interface d'administration simplifiée pour les utilisateurs SAR
    """
    
    # Configuration de la liste des utilisateurs
    list_display = [
        'username', 'full_name', 'email', 'phone_display', 'office_phone_display', 'position_display', 'department_display', 'manager_display', 'avatar_preview', 'is_active', 'last_login', 'created_at'
    ]
    
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'created_at', 'last_login'
    ]
    
    search_fields = [
        'first_name', 'last_name', 'email', 'username', 'phone_number', 'office_phone', 'position', 'department', 'manager__first_name', 'manager__last_name'
    ]
    
    ordering = ['last_name', 'first_name']
    
    # Configuration des champs en lecture seule
    readonly_fields = [
        'created_at', 'updated_at', 'last_login', 'date_joined', 'password_info', 'avatar_preview'
    ]
    
    # Configuration des champs dans le formulaire de détail
    fieldsets = (
        (_('Informations de connexion'), {
            'fields': ('username', 'email', 'password_info')
        }),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'office_phone', 'position', 'department', 'manager', 'avatar', 'avatar_preview')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuration pour l'ajout d'un nouvel utilisateur
    add_fieldsets = (
        (_('Informations de connexion'), {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'office_phone', 'position', 'department', 'manager')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    # Configuration des filtres horizontaux
    filter_horizontal = ('groups', 'user_permissions')
    
    # Actions personnalisées
    actions = ['activate_users', 'deactivate_users']
    
    def full_name(self, obj):
        """Affiche le nom complet de l'utilisateur"""
        return obj.get_full_name()
    full_name.short_description = 'Nom complet'
    full_name.admin_order_field = 'last_name'
    
    def phone_display(self, obj):
        """Affiche le numéro de téléphone personnel de manière lisible"""
        if obj.phone_number:
            return obj.phone_number
        return format_html('<span style="color: #6b7280; font-style: italic;">Non renseigné</span>')
    phone_display.short_description = 'Téléphone personnel'
    phone_display.admin_order_field = 'phone_number'
    
    def office_phone_display(self, obj):
        """Affiche le numéro de téléphone fixe de manière lisible"""
        if obj.office_phone:
            return obj.office_phone
        return format_html('<span style="color: #6b7280; font-style: italic;">Non renseigné</span>')
    office_phone_display.short_description = 'Téléphone fixe'
    office_phone_display.admin_order_field = 'office_phone'
    
    def position_display(self, obj):
        """Affiche le poste de manière lisible"""
        if obj.position:
            return obj.position
        return format_html('<span style="color: #6b7280; font-style: italic;">Non renseigné</span>')
    position_display.short_description = 'Poste'
    position_display.admin_order_field = 'position'
    
    def department_display(self, obj):
        """Affiche le département de manière lisible"""
        if obj.department:
            return obj.department
        return format_html('<span style="color: #6b7280; font-style: italic;">Non renseigné</span>')
    department_display.short_description = 'Département'
    department_display.admin_order_field = 'department'
    
    def manager_display(self, obj):
        """Affiche le manager de manière lisible"""
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}"
        return format_html('<span style="color: #6b7280; font-style: italic;">Aucun</span>')
    manager_display.short_description = 'Chef direct (N+1)'
    manager_display.admin_order_field = 'manager__last_name'
    
    def password_info(self, obj):
        """Affiche des informations sur le mot de passe"""
        if obj.pk:
            return format_html(
                '<a href="{}" class="button">Changer le mot de passe</a>',
                reverse('admin:auth_user_password_change', args=[obj.pk])
            )
        return 'Le mot de passe sera défini lors de la création'
    password_info.short_description = 'Mot de passe'
    
    def avatar_preview(self, obj):
        """Affiche un aperçu de l'avatar"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; border-radius: 50%; background-color: #e5e7eb; display: flex; align-items: center; justify-content: center; color: #6b7280; font-weight: bold;">{}</div>',
            obj.get_short_name()[:2].upper() if obj.get_short_name() else '??'
        )
    avatar_preview.short_description = 'Avatar'
    
    def activate_users(self, request, queryset):
        """Action pour activer les utilisateurs sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} utilisateur(s) activé(s) avec succès.')
    activate_users.short_description = 'Activer les utilisateurs sélectionnés'
    
    def deactivate_users(self, request, queryset):
        """Action pour désactiver les utilisateurs sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} utilisateur(s) désactivé(s) avec succès.')
    deactivate_users.short_description = 'Désactiver les utilisateurs sélectionnés'
    
    # Configuration de la pagination
    list_per_page = 25
    list_max_show_all = 100
    
    # Configuration des champs de recherche
    search_help_text = 'Rechercher par nom, prénom, email ou nom d\'utilisateur'
    
    # Configuration des messages d'aide
    def get_queryset(self, request):
        """Optimise les requêtes pour la liste des utilisateurs"""
        return super().get_queryset(request).select_related().prefetch_related('groups')
    
    def get_readonly_fields(self, request, obj=None):
        """Champs en lecture seule selon le contexte"""
        readonly_fields = list(self.readonly_fields)
        
        # Si c'est un super admin, il peut modifier les permissions
        if not request.user.is_superuser:
            readonly_fields.extend(['is_staff', 'is_superuser', 'groups', 'user_permissions'])
        
        return readonly_fields


# Configuration du site admin - Laissé à l'app annuaire pour éviter les conflits
# admin.site.site_header = "Administration SAR Intranet"
# admin.site.site_title = "SAR Admin"
# admin.site.index_title = "Tableau de bord d'administration"
