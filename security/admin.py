from django.contrib import admin
from .models import SecurityDocument

@admin.register(SecurityDocument)
class SecurityDocumentAdmin(admin.ModelAdmin):
    """
    Administration pour les documents de sécurité
    """
    list_display = [
        'title',
        'get_file_size_display',
        'uploaded_by',
        'created_at',
        'is_active',
    ]
    list_filter = [
        'is_active',
        'created_at',
        'uploaded_by',
    ]
    search_fields = [
        'title',
        'description',
    ]
    readonly_fields = [
        'file_size',
        'uploaded_by',
        'created_at',
        'updated_at',
        'get_file_size_display',
    ]
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'icon', 'is_active')
        }),
        ('Fichier', {
            'fields': ('file', 'file_size', 'get_file_size_display'),
            'description': 'Fichiers acceptés: PDF, JPG, JPEG, PNG, GIF, WEBP (max 50MB)'
        }),
        ('Métadonnées', {
            'fields': ('uploaded_by', 'created_at', 'updated_at')
        }),
    )
    ordering = ['order', '-created_at']
    
    def get_fieldsets(self, request, obj=None):
        """Retourne les fieldsets avec 'order' uniquement en modification"""
        fieldsets = list(super().get_fieldsets(request, obj))
        # Ajouter 'order' uniquement lors de la modification (pas lors de l'ajout)
        if obj:  # Si l'objet existe (modification)
            fieldsets[0][1]['fields'] = ('title', 'description', 'is_active')
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        """Surcharge pour calculer automatiquement file_size et définir uploaded_by"""
        # Calculer file_size si un fichier est fourni
        file_changed = False
        if hasattr(form, 'changed_data'):
            file_changed = 'file' in form.changed_data
        
        if obj.file:
            # Pour les nouveaux objets ou si le fichier a changé
            if not change or file_changed:
                # Les fichiers uploadés via formulaire Django ont un attribut 'size'
                if hasattr(obj.file, 'size'):
                    try:
                        file_size = obj.file.size
                        if file_size is not None and file_size > 0:
                            obj.file_size = file_size
                        else:
                            # Fallback: lire la taille manuellement
                            obj.file_size = self._get_file_size(obj.file)
                    except (AttributeError, TypeError):
                        obj.file_size = self._get_file_size(obj.file)
                else:
                    obj.file_size = self._get_file_size(obj.file)
            # Si c'est une modification et que le fichier n'a pas changé, file_size est déjà défini
        
        # S'assurer que file_size n'est jamais None (requis par la base de données)
        if not hasattr(obj, 'file_size') or obj.file_size is None:
            obj.file_size = 0
        
        # Définir uploaded_by si non défini
        if not obj.uploaded_by and request.user.is_authenticated:
            obj.uploaded_by = request.user
        
        super().save_model(request, obj, form, change)
    
    def _get_file_size(self, file_obj):
        """Méthode helper pour obtenir la taille d'un fichier"""
        try:
            if hasattr(file_obj, 'read'):
                current_pos = file_obj.tell()
                file_obj.seek(0, 2)  # Aller à la fin
                size = file_obj.tell()
                file_obj.seek(current_pos)  # Revenir à la position initiale
                return size
        except (AttributeError, IOError, ValueError):
            pass
        return 0
    
    def get_file_size_display(self, obj):
        """Affiche la taille formatée du fichier"""
        return obj.get_file_size_display()
    get_file_size_display.short_description = 'Taille du fichier'
