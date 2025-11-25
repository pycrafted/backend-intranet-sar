from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Department, Project
from .serializers import (
    SafetyDataSerializer, 
    SafetyDataCreateUpdateSerializer,
    IdeaSerializer,
    IdeaCreateSerializer,
    IdeaUpdateSerializer,
    DepartmentSerializer,
    MenuItemSerializer,
    MenuItemCreateUpdateSerializer,
    DayMenuSerializer,
    DayMenuCreateUpdateSerializer,
    WeekMenuSerializer,
    EventSerializer,
    EventCreateUpdateSerializer,
    EventListSerializer,
    ProjectSerializer,
    ProjectCreateUpdateSerializer
)


class SafetyDataListAPIView(generics.ListAPIView):
    """
    API endpoint pour récupérer les données de sécurité
    """
    serializer_class = SafetyDataSerializer
    queryset = SafetyData.objects.all()
    
    def get_queryset(self):
        # Retourner seulement la dernière entrée (il ne devrait y en avoir qu'une)
        return SafetyData.objects.all().order_by('-updated_at')[:1]


class SafetyDataDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint pour récupérer les détails d'une donnée de sécurité
    """
    serializer_class = SafetyDataSerializer
    queryset = SafetyData.objects.all()
    
    def get_object(self):
        # Retourner la dernière entrée ou créer une nouvelle si elle n'existe pas
        obj, created = SafetyData.objects.get_or_create(
            defaults={}
        )
        return obj


class SafetyDataUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour mettre à jour les données de sécurité
    """
    serializer_class = SafetyDataCreateUpdateSerializer
    queryset = SafetyData.objects.all()
    
    def get_object(self):
        # Retourner la dernière entrée ou créer une nouvelle si elle n'existe pas
        obj, created = SafetyData.objects.get_or_create(
            defaults={}
        )
        return obj


@api_view(['GET'])
def safety_data_current(request):
    """
    API endpoint pour récupérer les données de sécurité actuelles
    Retourne la dernière entrée ou crée une nouvelle si elle n'existe pas
    """
    try:
        # Récupérer ou créer les données de sécurité
        safety_data, created = SafetyData.objects.get_or_create(
            defaults={}
        )
        
        serializer = SafetyDataSerializer(safety_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des données de sécurité: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def safety_data_update(request):
    """
    API endpoint pour mettre à jour les données de sécurité
    """
    try:
        # Récupérer ou créer les données de sécurité
        safety_data, created = SafetyData.objects.get_or_create(
            defaults={}
        )
        
        # Traiter les données reçues
        data = request.data
        
        # Si on reçoit des jours sans accident, les convertir en dates d'accident
        if 'days_without_incident_sar' in data:
            from django.utils import timezone
            from datetime import timedelta
            days = data.get('days_without_incident_sar', 0)
            safety_data.last_incident_date_sar = timezone.now() - timedelta(days=days)
        
        if 'days_without_incident_ee' in data:
            from django.utils import timezone
            from datetime import timedelta
            days = data.get('days_without_incident_ee', 0)
            safety_data.last_incident_date_ee = timezone.now() - timedelta(days=days)
        
        # Mettre à jour les autres champs
        if 'last_incident_date_sar' in data:
            safety_data.last_incident_date_sar = data['last_incident_date_sar']
        if 'last_incident_date_ee' in data:
            safety_data.last_incident_date_ee = data['last_incident_date_ee']
        if 'last_incident_type_sar' in data:
            safety_data.last_incident_type_sar = data['last_incident_type_sar']
        if 'last_incident_type_ee' in data:
            safety_data.last_incident_type_ee = data['last_incident_type_ee']
        if 'last_incident_description_sar' in data:
            safety_data.last_incident_description_sar = data['last_incident_description_sar']
        if 'last_incident_description_ee' in data:
            safety_data.last_incident_description_ee = data['last_incident_description_ee']
        
        safety_data.save()
        
        # Retourner les données mises à jour
        response_serializer = SafetyDataSerializer(safety_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la mise à jour des données de sécurité: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def safety_data_reset(request):
    """
    API endpoint pour réinitialiser les données de sécurité
    """
    try:
        # Récupérer ou créer les données de sécurité
        safety_data, created = SafetyData.objects.get_or_create(
            defaults={}
        )
        
        # Réinitialiser les données en mettant les dates d'accident à maintenant
        from django.utils import timezone
        safety_data.last_incident_date_sar = timezone.now()
        safety_data.last_incident_date_ee = timezone.now()
        safety_data.save()
        
        serializer = SafetyDataSerializer(safety_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la réinitialisation des données de sécurité: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===== VUES POUR LES IDÉES =====

class IdeaListAPIView(generics.ListAPIView):
    """
    API endpoint pour lister les idées
    """
    serializer_class = IdeaSerializer
    queryset = Idea.objects.all()
    
    def get_queryset(self):
        # Filtrer par département si spécifié (peut être un code ou un ID)
        department = self.request.query_params.get('department', None)
        status_filter = self.request.query_params.get('status', None)
        
        queryset = Idea.objects.select_related('department').all()
        
        if department:
            # Essayer de trouver par code d'abord, puis par ID
            try:
                dept = Department.objects.get(code=department, is_active=True)
                queryset = queryset.filter(department=dept)
            except Department.DoesNotExist:
                try:
                    dept = Department.objects.get(id=department, is_active=True)
                    queryset = queryset.filter(department=dept)
                except (Department.DoesNotExist, ValueError):
                    pass  # Si aucun département trouvé, retourner toutes les idées
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-submitted_at')


class IdeaCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour créer une nouvelle idée
    """
    serializer_class = IdeaCreateSerializer
    queryset = Idea.objects.all()


class IdeaDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint pour récupérer les détails d'une idée
    """
    serializer_class = IdeaSerializer
    queryset = Idea.objects.all()


class IdeaUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour mettre à jour le statut d'une idée
    """
    serializer_class = IdeaUpdateSerializer
    queryset = Idea.objects.all()


class IdeaDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint pour supprimer une idée
    """
    queryset = Idea.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def idea_submit(request):
    """
    API endpoint pour soumettre une nouvelle idée
    """
    try:
        serializer = IdeaCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            idea = serializer.save()
            response_serializer = IdeaSerializer(idea)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la soumission de l\'idée: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def idea_departments(request):
    """
    API endpoint pour récupérer la liste des départements actifs
    """
    try:
        departments = Department.objects.filter(is_active=True).order_by('name')
        departments_data = [
            {
                'id': dept.id,
                'code': dept.code,
                'name': dept.name,
                'icon': get_department_icon(dept.code),
                'emails': dept.get_emails_list()
            }
            for dept in departments
        ]
        
        return Response(departments_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des départements: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_department_icon(department_code):
    """
    Retourne l'icône correspondant au code du département
    """
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
    return icons.get(department_code, '📋')


# ===== VUES POUR LES DÉPARTEMENTS =====

class DepartmentListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des départements
    """
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()
    
    def get_queryset(self):
        # Filtrer par is_active si spécifié
        is_active = self.request.query_params.get('is_active', None)
        queryset = Department.objects.all()
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')


class DepartmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer un département
    """
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()


# ===== VUES POUR LE MENU =====

class MenuItemListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer les plats
    """
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()
    
    def get_queryset(self):
        # Filtrer par type si spécifié
        menu_type = self.request.query_params.get('type', None)
        is_available = self.request.query_params.get('is_available', None)
        
        queryset = MenuItem.objects.all()
        
        if menu_type:
            queryset = queryset.filter(type=menu_type)
        
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        return queryset.order_by('type', 'name')


class MenuItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour et supprimer un plat
    """
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()


class DayMenuListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer les menus des jours
    """
    serializer_class = DayMenuSerializer
    queryset = DayMenu.objects.all()
    
    def get_queryset(self):
        # Filtrer par date si spécifié
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        is_active = self.request.query_params.get('is_active', None)
        
        queryset = DayMenu.objects.all()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('date', 'day')


class DayMenuDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour et supprimer un menu du jour
    """
    serializer_class = DayMenuSerializer
    queryset = DayMenu.objects.all()


@api_view(['GET'])
def week_menu(request):
    """
    API endpoint pour récupérer le menu de la semaine
    """
    try:
        from datetime import datetime, timedelta
        
        # Récupérer la date de début de semaine (lundi) de la semaine courante
        today = timezone.now().date()
        # Calculer le lundi de la semaine courante
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        thursday = monday + timedelta(days=3)
        
        # Récupérer les menus de la semaine (tous, pas seulement actifs)
        week_menus = DayMenu.objects.filter(
            date__gte=monday,
            date__lte=thursday
        ).order_by('date')
        
        serializer = DayMenuSerializer(week_menus, many=True)
        
        response_data = {
            'week_start': monday.isoformat(),
            'week_end': thursday.isoformat(),
            'days': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération du menu de la semaine: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def available_menu_items(request):
    """
    API endpoint pour récupérer les plats disponibles par type
    """
    try:
        menu_type = request.query_params.get('type', None)
        
        if menu_type:
            items = MenuItem.objects.filter(type=menu_type, is_available=True)
        else:
            items = MenuItem.objects.filter(is_available=True)
        
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des plats: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_week_menu(request):
    """
    API endpoint pour créer un menu de la semaine complète
    """
    try:
        from datetime import datetime, timedelta
        
        # Récupérer la date de début de semaine
        week_start_str = request.data.get('week_start')
        if not week_start_str:
            return Response(
                {'error': 'La date de début de semaine est obligatoire.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        input_date = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        
        # Calculer le lundi de la semaine de la date donnée
        days_since_monday = input_date.weekday()
        week_start = input_date - timedelta(days=days_since_monday)
        
        # Récupérer les données des menus
        menus_data = request.data.get('menus', [])
        
        # Vérifier qu'on a au moins un menu
        if len(menus_data) == 0:
            return Response(
                {'error': 'Au moins un menu est requis.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_menus = []
        
        # Créer les menus pour les jours restants de la semaine
        # Filtrer uniquement les menus complets (avec senegalese et european en texte)
        for menu_data in menus_data:
            # Vérifier que le menu est complet (a au moins un plat sénégalais et européen)
            senegalese = menu_data.get('senegalese', '').strip()
            european = menu_data.get('european', '').strip()
            
            # Ignorer les menus incomplets
            if not senegalese or not european:
                continue
            
            # Utiliser la date fournie par le frontend
            current_date = datetime.strptime(menu_data['date'], '%Y-%m-%d').date()
            
            # Permettre la création de menus pour TOUS les jours de la semaine courante
            # Inclure les jours passés, présents et futurs de la semaine
                
            # La date est déjà dans menu_data, pas besoin de la redéfinir
            
            # Vérifier si un menu existe déjà pour cette date
            existing_menu = DayMenu.objects.filter(date=current_date).first()
            if existing_menu:
                # Mettre à jour le menu existant
                serializer = DayMenuSerializer(existing_menu, data=menu_data, context={'request': request})
                if serializer.is_valid():
                    menu = serializer.save()
                    created_menus.append(menu)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Créer un nouveau menu
                serializer = DayMenuSerializer(data=menu_data, context={'request': request})
                if serializer.is_valid():
                    menu = serializer.save()
                    created_menus.append(menu)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Retourner tous les menus de la semaine (pas seulement ceux créés)
        week_menus = DayMenu.objects.filter(
            date__gte=week_start,
            date__lte=week_start + timedelta(days=3)
        ).order_by('date')
        
        response_serializer = DayMenuSerializer(week_menus, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la création du menu de la semaine: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== VUES POUR LES ÉVÉNEMENTS ====================

class EventListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des événements
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateUpdateSerializer
        return EventSerializer
    
    def get_queryset(self):
        queryset = Event.objects.all()
        
        # Filtrage par type
        event_type = self.request.query_params.get('type', None)
        if event_type:
            queryset = queryset.filter(type=event_type)
        
        # Filtrage par date (événements futurs uniquement)
        future_only = self.request.query_params.get('future_only', None)
        if future_only and future_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(date__gte=today)
        
        # Filtrage par mois et année
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        if year and month:
            queryset = queryset.filter(date__year=year, date__month=month)
        
        return queryset.order_by('date', 'time')


class EventDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, modifier et supprimer un événement
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EventCreateUpdateSerializer
        return EventSerializer
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


@api_view(['GET'])
def events_by_month(request, year, month):
    """
    API endpoint pour récupérer les événements d'un mois spécifique
    """
    try:
        events = Event.objects.filter(
            date__year=year,
            date__month=month
        ).order_by('date', 'time')
        
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des événements: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def next_event(request):
    """
    API endpoint pour récupérer le prochain événement
    """
    try:
        today = timezone.now().date()
        
        # Récupérer le prochain événement (aujourd'hui inclus)
        next_event = Event.objects.filter(
            date__gte=today
        ).order_by('date', 'time').first()
        
        if next_event:
            serializer = EventSerializer(next_event)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'message': 'Aucun événement prévu'}, 
                status=status.HTTP_200_OK
            )
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération du prochain événement: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def events_by_date(request, date):
    """
    API endpoint pour récupérer les événements d'une date spécifique
    Format de date attendu: YYYY-MM-DD
    """
    try:
        from datetime import datetime
        
        # Parser la date
        event_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        events = Event.objects.filter(date=event_date).order_by('time')
        serializer = EventSerializer(events, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except ValueError:
        return Response(
            {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des événements: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def event_stats(request):
    """
    API endpoint pour récupérer les statistiques des événements
    """
    try:
        today = timezone.now().date()
        
        # Statistiques générales
        total_events = Event.objects.count()
        future_events = Event.objects.filter(date__gte=today).count()
        past_events = Event.objects.filter(date__lt=today).count()
        today_events = Event.objects.filter(date=today).count()
        
        # Statistiques par type
        type_stats = {}
        for event_type, _ in Event.TYPE_CHOICES:
            count = Event.objects.filter(type=event_type).count()
            type_stats[event_type] = count
        
        # Prochain événement
        next_event = Event.objects.filter(
            date__gte=today
        ).order_by('date', 'time').first()
        
        next_event_data = None
        if next_event:
            next_event_data = {
                'title': next_event.title,
                'date': next_event.date.isoformat(),
                'time': next_event.time.strftime('%H:%M') if next_event.time else None,
                'type': next_event.type,
                'location': next_event.location
            }
        
        stats = {
            'total_events': total_events,
            'future_events': future_events,
            'past_events': past_events,
            'today_events': today_events,
            'type_stats': type_stats,
            'next_event': next_event_data
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des statistiques: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===== ENDPOINTS POUR LES PROJETS =====

class ProjectListAPIView(generics.ListCreateAPIView):
    """
    API endpoint pour lister et créer des projets
    """
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    
    def get_queryset(self):
        """Filtrer les projets et les trier par date de création"""
        queryset = Project.objects.all()
        
        # Filtre par statut si fourni
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon la méthode"""
        if self.request.method == 'POST':
            return ProjectCreateUpdateSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        """Créer un projet avec les données fournies"""
        serializer.save()


class ProjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer un projet
    """
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon la méthode"""
        if self.request.method in ['PUT', 'PATCH']:
            return ProjectCreateUpdateSerializer
        return ProjectSerializer
    
    def perform_update(self, serializer):
        """Mettre à jour un projet"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer le projet"""
        instance.delete()


@api_view(['GET'])
def projects_active(request):
    """
    API endpoint pour récupérer tous les projets
    Utile pour le widget de la page d'accueil
    """
    try:
        projects = Project.objects.all().order_by('-created_at')
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des projets: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
