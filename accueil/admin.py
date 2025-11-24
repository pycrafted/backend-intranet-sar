from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils import timezone
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Department, Project


@admin.register(SafetyData)
class SafetyDataAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les données de sécurité du travail
    """
    list_display = [
        'id',
        'get_days_without_incident_sar',
        'get_days_without_incident_ee',
        'get_appreciation_sar',
        'get_appreciation_ee',
        'updated_at'
    ]
    
    actions = ['reset_safety_data', 'simulate_sar_accident', 'simulate_ee_accident']
    
    list_filter = [
        'created_at',
        'updated_at'
    ]

    search_fields = [
        'last_incident_type_sar',
        'last_incident_type_ee',
        'last_incident_description_sar',
        'last_incident_description_ee'
    ]
    
    readonly_fields = [
        'get_appreciation_sar',
        'get_appreciation_ee',
        'get_days_without_incident_sar',
        'get_days_without_incident_ee',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Compteurs de Jours (Calculés automatiquement)', {
            'fields': (
                'get_days_without_incident_sar',
                'get_days_without_incident_ee',
                'get_appreciation_sar',
                'get_appreciation_ee'
            )
        }),
        ('Derniers Accidents SAR', {
            'fields': (
                'last_incident_date_sar',
                'last_incident_type_sar',
                'last_incident_description_sar'
            )
        }),
        ('Derniers Accidents EE', {
            'fields': (
                'last_incident_date_ee',
                'last_incident_type_ee',
                'last_incident_description_ee'
            )
        }),
        ('Informations Générales', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-updated_at']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def has_add_permission(self, request):
        """Permettre l'ajout si aucun enregistrement n'existe"""
        return SafetyData.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        """Permettre la suppression pour réinitialiser"""
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Champs en lecture seule selon le contexte"""
        if obj:  # Modification
            return self.readonly_fields
        return []  # Création
    
    def get_fieldsets(self, request, obj=None):
        """Fieldsets selon le contexte"""
        if obj:  # Modification - afficher tous les fieldsets
            return self.fieldsets
        else:  # Création - exclure les champs readonly
            return (
                ('Derniers Accidents SAR', {
                    'fields': (
                        'last_incident_date_sar',
                        'last_incident_type_sar',
                        'last_incident_description_sar'
                    )
                }),
                ('Derniers Accidents EE', {
                    'fields': (
                        'last_incident_date_ee',
                        'last_incident_type_ee',
                        'last_incident_description_ee'
                    )
                })
            )
    
    def save_model(self, request, obj, form, change):
        """Sauvegarder le modèle"""
        super().save_model(request, obj, form, change)
    
    def get_days_without_incident_sar(self, obj):
        """Afficher les jours sans accident SAR"""
        if obj:
            return f"{obj.days_without_incident_sar} jours"
        return "N/A"
    get_days_without_incident_sar.short_description = "Jours sans accident SAR"
    get_days_without_incident_sar.admin_order_field = 'last_incident_date_sar'
    
    def get_days_without_incident_ee(self, obj):
        """Afficher les jours sans accident EE"""
        if obj:
            return f"{obj.days_without_incident_ee} jours"
        return "N/A"
    get_days_without_incident_ee.short_description = "Jours sans accident EE"
    get_days_without_incident_ee.admin_order_field = 'last_incident_date_ee'
    
    def get_appreciation_sar(self, obj):
        """Afficher l'appréciation SAR"""
        if obj:
            return obj.appreciation_sar
        return "N/A"
    get_appreciation_sar.short_description = "Appréciation SAR"
    
    def get_appreciation_ee(self, obj):
        """Afficher l'appréciation EE"""
        if obj:
            return obj.appreciation_ee
        return "N/A"
    get_appreciation_ee.short_description = "Appréciation EE"
    
    def reset_safety_data(self, request, queryset):
        """Action pour réinitialiser les données de sécurité"""
        for obj in queryset:
            # Réinitialiser en mettant les dates d'accident à maintenant
            from django.utils import timezone
            obj.last_incident_date_sar = timezone.now()
            obj.last_incident_date_ee = timezone.now()
            obj.save()

        self.message_user(
            request,
            f"✅ {queryset.count()} enregistrement(s) de sécurité réinitialisé(s) avec succès!",
            messages.SUCCESS
        )
    reset_safety_data.short_description = "🔄 Réinitialiser les données de sécurité"

    def simulate_sar_accident(self, request, queryset):
        """Action pour simuler un accident SAR"""
        for obj in queryset:
            # Simuler un accident en mettant la date à maintenant
            from django.utils import timezone
            obj.last_incident_date_sar = timezone.now()
            obj.save()

        self.message_user(
            request,
            f"⚠️ {queryset.count()} accident(s) SAR simulé(s) - compteur remis à 0!",
            messages.WARNING
        )
    simulate_sar_accident.short_description = "⚠️ Simuler un accident SAR (remet à 0)"

    def simulate_ee_accident(self, request, queryset):
        """Action pour simuler un accident EE"""
        for obj in queryset:
            # Simuler un accident en mettant la date à maintenant
            from django.utils import timezone
            obj.last_incident_date_ee = timezone.now()
            obj.save()

        self.message_user(
            request,
            f"⚠️ {queryset.count()} accident(s) EE simulé(s) - compteur remis à 0!",
            messages.WARNING
        )
    simulate_ee_accident.short_description = "⚠️ Simuler un accident EE (remet à 0)"
    
    # class Media:
    #     css = {
    #         'all': ('admin/css/safety_admin.css',)
    #     }
    #     js = ('admin/js/safety_admin.js',)


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les idées soumises
    """
    list_display = [
        'id',
        'description_preview',
        'department_display',
        'status_display',
        'submitted_at',
        'updated_at'
    ]
    
    list_filter = [
        'department',
        'status',
        'submitted_at',
        'updated_at'
    ]
    
    search_fields = [
        'description',
        'department'
    ]
    
    readonly_fields = [
        'submitted_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informations de l\'idée', {
            'fields': (
                'description',
                'department',
                'status'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'submitted_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-submitted_at']
    
    actions = ['mark_under_review', 'mark_approved', 'mark_rejected', 'mark_implemented']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def description_preview(self, obj):
        """Afficher un aperçu de la description"""
        if len(obj.description) > 100:
            return f"{obj.description[:100]}..."
        return obj.description
    description_preview.short_description = 'Description'
    
    def department_display(self, obj):
        """Afficher le département avec icône"""
        icons = {
            'production': '🏭',
            'maintenance': '🔧',
            'quality': '✅',
            'safety': '🛡️',
            'logistics': '🚛',
            'it': '💻',
            'hr': '👥',
            'finance': '💰',
            'marketing': '📢',
            'other': '📋',
        }
        if obj.department:
            icon = icons.get(obj.department.code, '📋')
            return f"{icon} {obj.department.name}"
        return "N/A"
    department_display.short_description = 'Département'
    
    def status_display(self, obj):
        """Afficher le statut avec couleur"""
        colors = {
            'submitted': 'blue',
            'under_review': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'implemented': 'purple',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def mark_under_review(self, request, queryset):
        """Action pour marquer comme en cours d'examen"""
        updated = queryset.update(status='under_review')
        self.message_user(
            request,
            f"✅ {updated} idée(s) marquée(s) comme en cours d'examen.",
            messages.SUCCESS
        )
    mark_under_review.short_description = "🔍 Marquer comme en cours d'examen"
    
    def mark_approved(self, request, queryset):
        """Action pour marquer comme approuvée"""
        updated = queryset.update(status='approved')
        self.message_user(
            request,
            f"✅ {updated} idée(s) marquée(s) comme approuvée(s).",
            messages.SUCCESS
        )
    mark_approved.short_description = "✅ Marquer comme approuvée"
    
    def mark_rejected(self, request, queryset):
        """Action pour marquer comme rejetée"""
        updated = queryset.update(status='rejected')
        self.message_user(
            request,
            f"❌ {updated} idée(s) marquée(s) comme rejetée(s).",
            messages.WARNING
        )
    mark_rejected.short_description = "❌ Marquer comme rejetée"
    
    def mark_implemented(self, request, queryset):
        """Action pour marquer comme implémentée"""
        updated = queryset.update(status='implemented')
        self.message_user(
            request,
            f"🚀 {updated} idée(s) marquée(s) comme implémentée(s).",
            messages.SUCCESS
        )
    mark_implemented.short_description = "🚀 Marquer comme implémentée"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les plats du menu
    """
    list_display = [
        'id',
        'name',
        'type_display',
        'is_available',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'type',
        'is_available',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'name',
        'description'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informations du plat', {
            'fields': (
                'name',
                'type',
                'description',
                'is_available'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['type', 'name']
    
    actions = ['mark_available', 'mark_unavailable']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def type_display(self, obj):
        """Afficher le type avec icône"""
        icons = {
            'senegalese': '🇸🇳',
            'european': '🇪🇺',
        }
        icon = icons.get(obj.type, '🍽️')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = 'Type'
    
    def mark_available(self, request, queryset):
        """Action pour marquer comme disponible"""
        updated = queryset.update(is_available=True)
        self.message_user(
            request,
            f"✅ {updated} plat(s) marqué(s) comme disponible(s).",
            messages.SUCCESS
        )
    mark_available.short_description = "✅ Marquer comme disponible"
    
    def mark_unavailable(self, request, queryset):
        """Action pour marquer comme indisponible"""
        updated = queryset.update(is_available=False)
        self.message_user(
            request,
            f"❌ {updated} plat(s) marqué(s) comme indisponible(s).",
            messages.WARNING
        )
    mark_unavailable.short_description = "❌ Marquer comme indisponible"


@admin.register(DayMenu)
class DayMenuAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les menus des jours
    """
    list_display = [
        'id',
        'day_display',
        'date',
        'senegalese_name',
        'european_name',
        'dessert_name',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'day',
        'is_active',
        'date',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'senegalese__name',
        'european__name',
        'dessert__name',
        'date'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informations du menu', {
            'fields': (
                'day',
                'date',
                'senegalese',
                'european',
                'dessert',
                'is_active'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-date', 'day']
    
    actions = ['mark_active', 'mark_inactive']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('senegalese', 'european', 'dessert')
    
    def day_display(self, obj):
        """Afficher le jour avec icône"""
        icons = {
            'monday': '📅',
            'tuesday': '📅',
            'wednesday': '📅',
            'thursday': '📅',
            'saturday': '📅',
            'sunday': '📅',
        }
        icon = icons.get(obj.day, '📅')
        return f"{icon} {obj.get_day_display()}"
    day_display.short_description = 'Jour'
    
    def senegalese_name(self, obj):
        """Afficher le nom du plat sénégalais"""
        return f"🇸🇳 {obj.senegalese.name}"
    senegalese_name.short_description = 'Plat Sénégalais'
    
    def european_name(self, obj):
        """Afficher le nom du plat européen"""
        return f"🇪🇺 {obj.european.name}"
    european_name.short_description = 'Plat Européen'
    
    def dessert_name(self, obj):
        """Afficher le nom du dessert"""
        if obj.dessert:
            return f"🍰 {obj.dessert.name}"
        return "—"
    dessert_name.short_description = 'Dessert'
    
    def mark_active(self, request, queryset):
        """Action pour marquer comme actif"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"✅ {updated} menu(s) marqué(s) comme actif(s).",
            messages.SUCCESS
        )
    mark_active.short_description = "✅ Marquer comme actif"
    
    def mark_inactive(self, request, queryset):
        """Action pour marquer comme inactif"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"❌ {updated} menu(s) marqué(s) comme inactif(s).",
            messages.WARNING
        )
    mark_inactive.short_description = "❌ Marquer comme inactif"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les événements
    """
    list_display = [
        'id',
        'title',
        'type_display',
        'date',
        'time_display',
        'location',
        'attendees',
        'is_all_day',
        'is_future_display',
        'created_at'
    ]
    
    list_filter = [
        'type',
        'is_all_day',
        'date',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'title',
        'description',
        'location'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'is_past',
        'is_today',
        'is_future'
    ]
    
    fieldsets = (
        ('Informations de l\'événement', {
            'fields': (
                'title',
                'description',
                'type',
                'location',
                'attendees'
            )
        }),
        ('Date et heure', {
            'fields': (
                'date',
                'time',
                'is_all_day'
            )
        }),
        ('Statut', {
            'fields': (
                'is_past',
                'is_today',
                'is_future'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['date', 'time']
    
    actions = ['mark_all_day', 'mark_not_all_day']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def type_display(self, obj):
        """Afficher le type avec icône"""
        icons = {
            'meeting': '👥',
            'training': '🎓',
            'celebration': '🎉',
            'conference': '🎤',
            'other': '📅',
        }
        icon = icons.get(obj.type, '📅')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = 'Type'
    
    def time_display(self, obj):
        """Afficher l'heure formatée"""
        if obj.is_all_day:
            return "Toute la journée"
        elif obj.time:
            return obj.time.strftime('%H:%M')
        return "-"
    time_display.short_description = 'Heure'
    
    def is_future_display(self, obj):
        """Afficher le statut temporel avec couleur"""
        if obj.is_past:
            return format_html(
                '<span style="color: red; font-weight: bold;">Passé</span>'
            )
        elif obj.is_today:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Aujourd\'hui</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">Futur</span>'
            )
    is_future_display.short_description = 'Statut'
    
    def mark_all_day(self, request, queryset):
        """Action pour marquer comme toute la journée"""
        updated = queryset.update(is_all_day=True, time=None)
        self.message_user(
            request,
            f"✅ {updated} événement(s) marqué(s) comme toute la journée.",
            messages.SUCCESS
        )
    mark_all_day.short_description = "📅 Marquer comme toute la journée"
    
    def mark_not_all_day(self, request, queryset):
        """Action pour marquer comme événement avec heure"""
        updated = queryset.update(is_all_day=False)
        self.message_user(
            request,
            f"⏰ {updated} événement(s) marqué(s) comme événement avec heure.",
            messages.SUCCESS
        )
    mark_not_all_day.short_description = "⏰ Marquer comme événement avec heure"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Administration des départements
    """
    list_display = ['code', 'name', 'is_active', 'emails_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('code', 'name', 'is_active')
        }),
        ('Emails', {
            'fields': ('emails',),
            'description': 'Liste des emails associés au département (format JSON: ["email1@example.com", "email2@example.com"])'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def emails_count(self, obj):
        """Affiche le nombre d'emails configurés"""
        emails = obj.get_emails_list()
        return len(emails)
    emails_count.short_description = 'Nombre d\'emails'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les projets stratégiques
    """
    list_display = [
        'id',
        'titre',
        'status',
        'chef_projet',
        'date_debut',
        'date_fin',
    ]
    
    list_filter = [
        'status',
        'created_at',
    ]
    
    search_fields = [
        'titre',
        'objective',
        'description',
        'chef_projet',
        'partners'
    ]
    
    readonly_fields = [
        'duration_days',
        'duration_formatted'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'objective', 'description', 'status')
        }),
        ('Dates et durée', {
            'fields': ('date_debut', 'date_fin', 'duration_days', 'duration_formatted')
        }),
        ('Partenaires', {
            'fields': ('partners',)
        }),
        ('Responsable', {
            'fields': ('chef_projet',)
        }),
        ('Image', {
            'fields': ('image',),
            'description': 'Vous pouvez uploader une image pour le projet'
        }),
    )
    
    def duration_days(self, obj):
        """Affiche la durée en jours"""
        return obj.duration_days or "N/A"
    duration_days.short_description = 'Durée (jours)'
    
    def duration_formatted(self, obj):
        """Affiche la durée formatée"""
        return obj.duration_formatted or "N/A"
    duration_formatted.short_description = 'Durée formatée'


