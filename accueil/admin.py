from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils import timezone
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Questionnaire, Question, QuestionnaireResponse, QuestionResponse


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
        icon = icons.get(obj.department, '📋')
        return f"{icon} {obj.get_department_display()}"
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
        return super().get_queryset(request).select_related('senegalese', 'european')
    
    def day_display(self, obj):
        """Afficher le jour avec icône"""
        icons = {
            'monday': '📅',
            'tuesday': '📅',
            'wednesday': '📅',
            'thursday': '📅',
            'friday': '📅',
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


# ===== ADMIN POUR LES QUESTIONNAIRES =====

class QuestionInline(admin.TabularInline):
    """
    Inline pour les questions dans l'admin des questionnaires
    """
    model = Question
    extra = 0
    fields = ['order', 'text', 'type', 'is_required', 'options']
    ordering = ['order']


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les questionnaires
    """
    list_display = [
        'id',
        'title',
        'type_display',
        'status_display',
        'target_audience_display',
        'is_active_display',
        'total_responses',
        'created_by_name',
        'created_at'
    ]
    
    list_filter = [
        'type',
        'status',
        'target_audience_type',
        'is_anonymous',
        'created_at',
        'start_date',
        'end_date'
    ]
    
    search_fields = [
        'title',
        'description',
        'created_by__first_name',
        'created_by__last_name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'total_responses',
        'is_active_display'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'title',
                'description',
                'type',
                'status'
            )
        }),
        ('Configuration', {
            'fields': (
                'is_anonymous',
                'allow_multiple_responses',
                'show_results_after_submission'
            )
        }),
        ('Ciblage', {
            'fields': (
                'target_audience_type',
                'target_departments',
                'target_roles'
            )
        }),
        ('Dates', {
            'fields': (
                'start_date',
                'end_date'
            )
        }),
        ('Statistiques', {
            'fields': (
                'total_responses',
                'is_active_display'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [QuestionInline]
    
    ordering = ['-created_at']
    
    actions = ['activate_questionnaires', 'deactivate_questionnaires', 'duplicate_questionnaire']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('created_by').prefetch_related('questions')
    
    def type_display(self, obj):
        """Afficher le type avec icône"""
        icons = {
            'survey': '📊',
            'quiz': '🧠',
            'evaluation': '⭐',
            'feedback': '💬',
            'poll': '📋',
        }
        icon = icons.get(obj.type, '📋')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = 'Type'
    
    def status_display(self, obj):
        """Afficher le statut avec couleur"""
        colors = {
            'draft': 'gray',
            'active': 'green',
            'paused': 'orange',
            'closed': 'red',
            'archived': 'purple',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def target_audience_display(self, obj):
        """Afficher l'audience ciblée"""
        if obj.target_audience_type == 'all':
            return "🌍 Tous les employés"
        elif obj.target_audience_type == 'department':
            depts = ', '.join(obj.target_departments) if obj.target_departments else 'Aucun'
            return f"🏢 Départements: {depts}"
        elif obj.target_audience_type == 'role':
            roles = ', '.join(obj.target_roles) if obj.target_roles else 'Aucun'
            return f"👔 Rôles: {roles}"
        else:
            return "🎯 Personnalisé"
    target_audience_display.short_description = 'Audience'
    
    def is_active_display(self, obj):
        """Afficher le statut actif"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Actif</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ Inactif</span>'
            )
    is_active_display.short_description = 'Actif'
    
    def created_by_name(self, obj):
        """Afficher le nom du créateur"""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return "Anonyme"
    created_by_name.short_description = 'Créé par'
    
    def activate_questionnaires(self, request, queryset):
        """Action pour activer les questionnaires"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f"✅ {updated} questionnaire(s) activé(s).",
            messages.SUCCESS
        )
    activate_questionnaires.short_description = "✅ Activer les questionnaires"
    
    def deactivate_questionnaires(self, request, queryset):
        """Action pour désactiver les questionnaires"""
        updated = queryset.update(status='paused')
        self.message_user(
            request,
            f"⏸️ {updated} questionnaire(s) mis en pause.",
            messages.WARNING
        )
    deactivate_questionnaires.short_description = "⏸️ Mettre en pause"
    
    def duplicate_questionnaire(self, request, queryset):
        """Action pour dupliquer un questionnaire"""
        for questionnaire in queryset:
            # Créer une copie du questionnaire
            new_questionnaire = Questionnaire.objects.create(
                title=f"{questionnaire.title} (Copie)",
                description=questionnaire.description,
                type=questionnaire.type,
                status='draft',
                is_anonymous=questionnaire.is_anonymous,
                allow_multiple_responses=questionnaire.allow_multiple_responses,
                show_results_after_submission=questionnaire.show_results_after_submission,
                target_audience_type=questionnaire.target_audience_type,
                target_departments=questionnaire.target_departments,
                target_roles=questionnaire.target_roles,
                created_by=request.user
            )
            
            # Copier les questions
            for question in questionnaire.questions.all():
                Question.objects.create(
                    questionnaire=new_questionnaire,
                    text=question.text,
                    type=question.type,
                    is_required=question.is_required,
                    order=question.order,
                    options=question.options,
                    scale_min=question.scale_min,
                    scale_max=question.scale_max,
                    scale_labels=question.scale_labels,
                    depends_on_question=question.depends_on_question,
                    show_condition=question.show_condition
                )
        
        self.message_user(
            request,
            f"📋 {queryset.count()} questionnaire(s) dupliqué(s).",
            messages.SUCCESS
        )
    duplicate_questionnaire.short_description = "📋 Dupliquer les questionnaires"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les questions
    """
    list_display = [
        'id',
        'questionnaire_title',
        'order',
        'text_preview',
        'type_display',
        'is_required',
        'created_at'
    ]
    
    list_filter = [
        'type',
        'is_required',
        'questionnaire__type',
        'questionnaire__status',
        'created_at'
    ]
    
    search_fields = [
        'text',
        'questionnaire__title'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informations de la question', {
            'fields': (
                'questionnaire',
                'text',
                'type',
                'is_required',
                'order'
            )
        }),
        ('Configuration spécifique', {
            'fields': (
                'options',
                'scale_min',
                'scale_max',
                'scale_labels'
            ),
            'classes': ('collapse',)
        }),
        ('Logique conditionnelle', {
            'fields': (
                'depends_on_question',
                'show_condition'
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
    
    ordering = ['questionnaire', 'order']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('questionnaire')
    
    def questionnaire_title(self, obj):
        """Afficher le titre du questionnaire"""
        return obj.questionnaire.title
    questionnaire_title.short_description = 'Questionnaire'
    
    def text_preview(self, obj):
        """Afficher un aperçu du texte de la question"""
        if len(obj.text) > 50:
            return f"{obj.text[:50]}..."
        return obj.text
    text_preview.short_description = 'Question'
    
    def type_display(self, obj):
        """Afficher le type avec icône"""
        icons = {
            'text': '📝',
            'single_choice': '🔘',
            'multiple_choice': '☑️',
            'scale': '📊',
            'date': '📅',
            'file': '📎',
            'rating': '⭐',
        }
        icon = icons.get(obj.type, '❓')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = 'Type'


@admin.register(QuestionnaireResponse)
class QuestionnaireResponseAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les réponses aux questionnaires
    """
    list_display = [
        'id',
        'questionnaire_title',
        'user_name',
        'submitted_at',
        'ip_address',
        'is_anonymous'
    ]
    
    list_filter = [
        'questionnaire__type',
        'questionnaire__status',
        'submitted_at',
        'user'
    ]
    
    search_fields = [
        'questionnaire__title',
        'user__first_name',
        'user__last_name',
        'ip_address'
    ]
    
    readonly_fields = [
        'submitted_at',
        'ip_address',
        'user_agent'
    ]
    
    fieldsets = (
        ('Informations de la réponse', {
            'fields': (
                'questionnaire',
                'user',
                'session_key'
            )
        }),
        ('Métadonnées techniques', {
            'fields': (
                'submitted_at',
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-submitted_at']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('questionnaire', 'user')
    
    def questionnaire_title(self, obj):
        """Afficher le titre du questionnaire"""
        return obj.questionnaire.title
    questionnaire_title.short_description = 'Questionnaire'
    
    def user_name(self, obj):
        """Afficher le nom de l'utilisateur"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Anonyme"
    user_name.short_description = 'Utilisateur'
    
    def is_anonymous(self, obj):
        """Afficher si la réponse est anonyme"""
        return not bool(obj.user)
    is_anonymous.boolean = True
    is_anonymous.short_description = 'Anonyme'


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les réponses aux questions
    """
    list_display = [
        'id',
        'questionnaire_title',
        'question_text_preview',
        'answer_preview',
        'created_at'
    ]
    
    list_filter = [
        'question__type',
        'question__questionnaire__type',
        'created_at'
    ]
    
    search_fields = [
        'question__text',
        'question__questionnaire__title',
        'answer_data'
    ]
    
    readonly_fields = [
        'created_at',
        'answer_data'
    ]
    
    fieldsets = (
        ('Informations de la réponse', {
            'fields': (
                'response',
                'question',
                'answer_data'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('response__questionnaire', 'question')
    
    def questionnaire_title(self, obj):
        """Afficher le titre du questionnaire"""
        return obj.response.questionnaire.title
    questionnaire_title.short_description = 'Questionnaire'
    
    def question_text_preview(self, obj):
        """Afficher un aperçu du texte de la question"""
        if len(obj.question.text) > 50:
            return f"{obj.question.text[:50]}..."
        return obj.question.text
    question_text_preview.short_description = 'Question'
    
    def answer_preview(self, obj):
        """Afficher un aperçu de la réponse"""
        answer = obj.answer_data
        if isinstance(answer, list):
            return ', '.join(str(item) for item in answer[:3]) + ('...' if len(answer) > 3 else '')
        elif isinstance(answer, str) and len(answer) > 50:
            return f"{answer[:50]}..."
        else:
            return str(answer)
    answer_preview.short_description = 'Réponse'
