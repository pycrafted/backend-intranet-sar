from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class UserAdmin(BaseUserAdmin):
    """Administration personnalisée pour le modèle User avec le champ matricule"""   
    
    # Ajouter les champs personnalisés dans la section "Personal info"
    # Le champ is_active est masqué car tous les comptes sont toujours actifs
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'matricule', 'position', 'phone_number', 'phone_fixed', 'department', 'avatar', 'manager')}),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            # is_active est masqué car tous les comptes sont toujours actifs
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
    # is_active est toujours True donc on peut l'afficher pour information
    list_display = ('username', 'email', 'first_name', 'last_name', 'matricule', 'position', 'department', 'phone_number', 'phone_fixed', 'is_staff', 'is_active')
    
    # Champs de recherche
    search_fields = ('username', 'email', 'first_name', 'last_name', 'matricule', 'position', 'phone_number', 'phone_fixed')
    
    # Filtres (is_active est toujours True donc peu utile, mais on le garde pour compatibilité)
    list_filter = ('is_staff', 'is_superuser', 'groups', 'department', 'position')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Rendre is_active, is_staff et is_superuser en lecture seule (ils sont toujours True)
        """
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Si on modifie un utilisateur existant
            readonly.extend(['is_active', 'is_staff', 'is_superuser'])
        else:  # Si on crée un nouvel utilisateur
            readonly.extend(['is_staff', 'is_superuser'])
        return readonly
    
    def get_fieldsets(self, request, obj=None):
        """
        Masquer le champ is_active dans l'admin car il est toujours True
        """
        fieldsets = super().get_fieldsets(request, obj)
        # Retirer is_active des fieldsets car il est toujours True
        # On le force dans le modèle User.save()
        return fieldsets


admin.site.register(User, UserAdmin)

