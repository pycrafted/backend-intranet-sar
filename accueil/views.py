from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from .models import SafetyData, Idea, MenuItem, DayMenu, Event, Questionnaire, Question, QuestionnaireResponse, QuestionResponse
from .serializers import (
    SafetyDataSerializer, 
    SafetyDataCreateUpdateSerializer,
    IdeaSerializer,
    IdeaCreateSerializer,
    IdeaUpdateSerializer,
    MenuItemSerializer,
    MenuItemCreateUpdateSerializer,
    DayMenuSerializer,
    DayMenuCreateUpdateSerializer,
    WeekMenuSerializer,
    EventSerializer,
    EventCreateUpdateSerializer,
    EventListSerializer,
    QuestionnaireSerializer,
    QuestionnaireCreateUpdateSerializer,
    QuestionnaireListSerializer,
    QuestionSerializer,
    QuestionCreateUpdateSerializer,
    QuestionnaireResponseSerializer,
    QuestionnaireResponseCreateSerializer
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
        # Filtrer par département si spécifié
        department = self.request.query_params.get('department', None)
        status_filter = self.request.query_params.get('status', None)
        
        queryset = Idea.objects.all()
        
        if department:
            queryset = queryset.filter(department=department)
        
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
    API endpoint pour récupérer la liste des départements
    """
    try:
        departments = [
            {
                'id': choice[0],
                'name': choice[1],
                'icon': get_department_icon(choice[0])
            }
            for choice in Idea.DEPARTMENT_CHOICES
        ]
        
        return Response(departments, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des départements: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_department_icon(department_id):
    """
    Retourne l'icône correspondant au département
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
    return icons.get(department_id, '📋')


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
        friday = monday + timedelta(days=4)
        
        # Récupérer les menus de la semaine (tous, pas seulement actifs)
        week_menus = DayMenu.objects.filter(
            date__gte=monday,
            date__lte=friday
        ).order_by('date')
        
        serializer = DayMenuSerializer(week_menus, many=True)
        
        response_data = {
            'week_start': monday.isoformat(),
            'week_end': friday.isoformat(),
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
        for menu_data in menus_data:
            # Utiliser la date fournie par le frontend
            current_date = datetime.strptime(menu_data['date'], '%Y-%m-%d').date()
            
            # Permettre la création de menus pour TOUS les jours de la semaine courante
            # Inclure les jours passés, présents et futurs de la semaine
                
            # La date est déjà dans menu_data, pas besoin de la redéfinir
            
            # Vérifier si un menu existe déjà pour cette date
            existing_menu = DayMenu.objects.filter(date=current_date).first()
            if existing_menu:
                # Mettre à jour le menu existant
                serializer = DayMenuSerializer(existing_menu, data=menu_data)
                if serializer.is_valid():
                    menu = serializer.save()
                    created_menus.append(menu)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Créer un nouveau menu
                serializer = DayMenuSerializer(data=menu_data)
                if serializer.is_valid():
                    menu = serializer.save()
                    created_menus.append(menu)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Retourner tous les menus de la semaine (pas seulement ceux créés)
        week_menus = DayMenu.objects.filter(
            date__gte=week_start,
            date__lte=week_start + timedelta(days=4)
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


# ===== VUES POUR LES QUESTIONNAIRES =====

class QuestionnaireListAPIView(generics.ListAPIView):
    """
    API endpoint pour lister les questionnaires
    """
    serializer_class = QuestionnaireListSerializer
    queryset = Questionnaire.objects.all()
    
    def get_queryset(self):
        queryset = Questionnaire.objects.all()
        
        # Filtrer par statut
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrer par type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        # Filtrer par audience
        audience_filter = self.request.query_params.get('audience')
        if audience_filter:
            queryset = queryset.filter(target_audience_type=audience_filter)
        
        # Filtrer les questionnaires actifs
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            )
        
        return queryset.order_by('-created_at')


class QuestionnaireDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint pour récupérer les détails d'un questionnaire
    """
    serializer_class = QuestionnaireSerializer
    queryset = Questionnaire.objects.all()


class QuestionnaireCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour créer un questionnaire
    """
    serializer_class = QuestionnaireCreateUpdateSerializer
    
    def perform_create(self, serializer):
        # Assigner l'utilisateur connecté comme créateur
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            # Retourner le questionnaire avec ses questions
            questionnaire = Questionnaire.objects.get(id=response.data['id'])
            serializer = QuestionnaireSerializer(questionnaire)
            response.data = serializer.data
        return response


class QuestionnaireUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour modifier un questionnaire
    """
    serializer_class = QuestionnaireCreateUpdateSerializer
    queryset = Questionnaire.objects.all()


class QuestionnaireDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint pour supprimer un questionnaire
    """
    queryset = Questionnaire.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionListAPIView(generics.ListAPIView):
    """
    API endpoint pour lister les questions d'un questionnaire
    """
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        questionnaire_id = self.kwargs['questionnaire_id']
        return Question.objects.filter(questionnaire_id=questionnaire_id).order_by('order')


class QuestionCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour créer une question
    """
    serializer_class = QuestionCreateUpdateSerializer
    
    def perform_create(self, serializer):
        questionnaire_id = self.kwargs['questionnaire_id']
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        serializer.save(questionnaire=questionnaire)


class QuestionUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint pour modifier une question
    """
    serializer_class = QuestionCreateUpdateSerializer
    queryset = Question.objects.all()


class QuestionDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint pour supprimer une question
    """
    queryset = Question.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionnaireResponseListAPIView(generics.ListAPIView):
    """
    API endpoint pour lister les réponses à un questionnaire
    """
    serializer_class = QuestionnaireResponseSerializer
    
    def get_queryset(self):
        questionnaire_id = self.kwargs['questionnaire_id']
        return QuestionnaireResponse.objects.filter(questionnaire_id=questionnaire_id).order_by('-submitted_at')


class QuestionnaireResponseCreateAPIView(generics.CreateAPIView):
    """
    API endpoint pour soumettre une réponse à un questionnaire
    """
    serializer_class = QuestionnaireResponseCreateSerializer
    
    def perform_create(self, serializer):
        # Ajouter les informations de session et IP
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=self.request.session.session_key or '',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
def questionnaire_stats(request, questionnaire_id):
    """
    API endpoint pour récupérer les statistiques d'un questionnaire
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        
        # Statistiques de base
        total_responses = questionnaire.total_responses
        
        # Statistiques par question
        question_stats = []
        for question in questionnaire.questions.all():
            question_responses = QuestionResponse.objects.filter(question=question)
            
            if question.type in ['single_choice', 'multiple_choice']:
                # Compter les réponses par option
                option_counts = {}
                for response in question_responses:
                    answers = response.answer_data
                    if isinstance(answers, list):
                        for answer in answers:
                            option_counts[answer] = option_counts.get(answer, 0) + 1
                    else:
                        option_counts[answers] = option_counts.get(answers, 0) + 1
                
                # Calculer les pourcentages
                total_question_responses = question_responses.count()
                option_percentages = {}
                for option, count in option_counts.items():
                    percentage = (count / total_question_responses * 100) if total_question_responses > 0 else 0
                    option_percentages[option] = round(percentage, 1)
                
                question_stats.append({
                    'question_id': question.id,
                    'question_text': question.text,
                    'question_type': question.type,
                    'total_responses': total_question_responses,
                    'option_counts': option_counts,
                    'option_percentages': option_percentages
                })
            
            elif question.type == 'scale':
                # Calculer la moyenne pour les échelles
                scale_values = []
                for response in question_responses:
                    answer = response.answer_data
                    if isinstance(answer, (int, float)):
                        scale_values.append(answer)
                
                if scale_values:
                    average = sum(scale_values) / len(scale_values)
                    question_stats.append({
                        'question_id': question.id,
                        'question_text': question.text,
                        'question_type': question.type,
                        'total_responses': len(scale_values),
                        'average': round(average, 2),
                        'min': min(scale_values),
                        'max': max(scale_values)
                    })
        
        stats = {
            'questionnaire_id': questionnaire.id,
            'questionnaire_title': questionnaire.title,
            'total_responses': total_responses,
            'question_stats': question_stats
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des statistiques: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def active_questionnaires(request):
    """
    API endpoint pour récupérer les questionnaires actifs pour la page d'accueil
    """
    try:
        now = timezone.now()
        
        # Récupérer les questionnaires actifs
        # Un questionnaire est actif si :
        # 1. Statut = 'active'
        # 2. Pas de date de début OU date de début <= maintenant
        # 3. Pas de date de fin OU date de fin >= maintenant
        questionnaires = Questionnaire.objects.filter(
            status='active'
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).order_by('-created_at')
        
        # Sérialiser avec les questions
        serializer = QuestionnaireSerializer(questionnaires, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des questionnaires actifs: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def questionnaire_statistics(request):
    """
    API endpoint pour récupérer les statistiques globales des questionnaires
    """
    try:
        # Statistiques de base
        total_questionnaires = Questionnaire.objects.count()
        active_questionnaires = Questionnaire.objects.filter(status='active').count()
        total_responses = QuestionnaireResponse.objects.count()
        
        # Calculer le taux de participation moyen
        questionnaires_with_responses = Questionnaire.objects.annotate(
            response_count=Count('responses')
        ).filter(response_count__gt=0)
        
        if questionnaires_with_responses.exists():
            average_response_rate = sum(
                q.response_rate for q in questionnaires_with_responses
            ) / questionnaires_with_responses.count()
        else:
            average_response_rate = 0
        
        # Répartition par statut
        status_counts = {}
        for status_choice, _ in Questionnaire.STATUS_CHOICES:
            status_counts[status_choice] = Questionnaire.objects.filter(status=status_choice).count()
        
        # Répartition par type
        type_counts = {}
        for type_name, _ in Questionnaire.TYPE_CHOICES:
            type_counts[type_name] = Questionnaire.objects.filter(type=type_name).count()
        
        # Enquêtes récentes (5 dernières)
        recent_questionnaires = Questionnaire.objects.order_by('-created_at')[:5]
        recent_serializer = QuestionnaireListSerializer(recent_questionnaires, many=True)
        
        # Enquêtes les plus populaires (par nombre de réponses)
        top_questionnaires = Questionnaire.objects.annotate(
            response_count=Count('responses')
        ).order_by('-response_count')[:5]
        top_serializer = QuestionnaireListSerializer(top_questionnaires, many=True)
        
        return Response({
            'total_questionnaires': total_questionnaires,
            'active_questionnaires': active_questionnaires,
            'total_responses': total_responses,
            'average_response_rate': round(average_response_rate, 2),
            'questionnaires_by_status': status_counts,
            'questionnaires_by_type': type_counts,
            'recent_questionnaires': recent_serializer.data,
            'top_questionnaires': top_serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des statistiques: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def questionnaire_analytics(request, pk):
    """
    API endpoint pour récupérer les analytics avancés d'un questionnaire
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, id=pk)
        
        # Analytics de base
        total_responses = questionnaire.total_responses
        response_rate = questionnaire.response_rate
        
        # Analytics par question avec plus de détails
        question_analytics = []
        for question in questionnaire.questions.all().order_by('order'):
            question_responses = QuestionResponse.objects.filter(question=question)
            total_question_responses = question_responses.count()
            
            analytics_data = {
                'question_id': question.id,
                'question_text': question.text,
                'question_type': question.type,
                'question_type_display': question.get_type_display(),
                'is_required': question.is_required,
                'order': question.order,
                'total_responses': total_question_responses,
                'response_rate': (total_question_responses / total_responses * 100) if total_responses > 0 else 0
            }
            
            if question.type in ['single_choice', 'multiple_choice']:
                # Compter les réponses par option
                option_counts = {}
                for response in question_responses:
                    answers = response.answer_data
                    if isinstance(answers, list):
                        for answer in answers:
                            option_counts[answer] = option_counts.get(answer, 0) + 1
                    else:
                        option_counts[answers] = option_counts.get(answers, 0) + 1
                
                # Calculer les pourcentages
                option_percentages = {}
                for option, count in option_counts.items():
                    percentage = (count / total_question_responses * 100) if total_question_responses > 0 else 0
                    option_percentages[option] = round(percentage, 1)
                
                analytics_data.update({
                    'option_counts': option_counts,
                    'option_percentages': option_percentages,
                    'most_popular_option': max(option_counts.items(), key=lambda x: x[1])[0] if option_counts else None,
                    'least_popular_option': min(option_counts.items(), key=lambda x: x[1])[0] if option_counts else None
                })
            
            elif question.type == 'scale':
                # Calculer les statistiques pour les échelles
                scale_values = []
                for response in question_responses:
                    answer = response.answer_data
                    if isinstance(answer, (int, float)):
                        scale_values.append(answer)
                
                if scale_values:
                    analytics_data.update({
                        'average': round(sum(scale_values) / len(scale_values), 2),
                        'min': min(scale_values),
                        'max': max(scale_values),
                        'median': sorted(scale_values)[len(scale_values) // 2],
                        'standard_deviation': round(
                            (sum((x - sum(scale_values) / len(scale_values)) ** 2 for x in scale_values) / len(scale_values)) ** 0.5, 2
                        ) if len(scale_values) > 1 else 0
                    })
            
            elif question.type == 'text':
                # Analyser les réponses textuelles
                text_responses = [response.answer_data for response in question_responses if response.answer_data]
                analytics_data.update({
                    'text_responses': text_responses,
                    'average_length': round(sum(len(str(resp)) for resp in text_responses) / len(text_responses), 1) if text_responses else 0,
                    'word_count': sum(len(str(resp).split()) for resp in text_responses) if text_responses else 0
                })
            
            question_analytics.append(analytics_data)
        
        # Analytics temporels
        responses_by_date = QuestionnaireResponse.objects.filter(questionnaire=questionnaire).extra(
            select={'date': 'DATE(submitted_at)'}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        # Analytics de performance
        performance_metrics = {
            'completion_rate': (total_responses / questionnaire.questions.count()) if questionnaire.questions.count() > 0 else 0,
            'average_time_per_question': 0,  # À calculer si on a les timestamps
            'drop_off_rate': 0,  # À calculer
            'most_answered_question': max(question_analytics, key=lambda x: x['total_responses'])['question_id'] if question_analytics else None,
            'least_answered_question': min(question_analytics, key=lambda x: x['total_responses'])['question_id'] if question_analytics else None
        }
        
        return Response({
            'questionnaire_id': questionnaire.id,
            'questionnaire_title': questionnaire.title,
            'questionnaire_type': questionnaire.type,
            'questionnaire_status': questionnaire.status,
            'total_responses': total_responses,
            'response_rate': response_rate,
            'question_analytics': question_analytics,
            'responses_by_date': list(responses_by_date),
            'performance_metrics': performance_metrics,
            'created_at': questionnaire.created_at,
            'updated_at': questionnaire.updated_at
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def questionnaire_export(request, pk):
    """
    API endpoint pour exporter les données d'un questionnaire
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, id=pk)
        format_type = request.GET.get('format', 'json')
        
        if format_type == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="questionnaire_{pk}_export.csv"'
            
            writer = csv.writer(response)
            
            # En-têtes
            headers = ['Question', 'Type', 'Réponse', 'Date de soumission', 'Utilisateur']
            writer.writerow(headers)
            
            # Données
            for question in questionnaire.questions.all():
                for response in QuestionResponse.objects.filter(question=question):
                    user_info = response.questionnaire_response.user.username if response.questionnaire_response.user else 'Anonyme'
                    writer.writerow([
                        question.text,
                        question.get_type_display(),
                        str(response.answer_data),
                        response.questionnaire_response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                        user_info
                    ])
            
            return response
        
        else:  # JSON par défaut
            # Récupérer toutes les données
            questionnaire_data = {
                'questionnaire': {
                    'id': questionnaire.id,
                    'title': questionnaire.title,
                    'description': questionnaire.description,
                    'type': questionnaire.type,
                    'status': questionnaire.status,
                    'created_at': questionnaire.created_at,
                    'updated_at': questionnaire.updated_at
                },
                'questions': [],
                'responses': []
            }
            
            # Questions
            for question in questionnaire.questions.all():
                question_data = {
                    'id': question.id,
                    'text': question.text,
                    'type': question.type,
                    'is_required': question.is_required,
                    'order': question.order,
                    'options': question.options
                }
                questionnaire_data['questions'].append(question_data)
            
            # Réponses
            for response in QuestionnaireResponse.objects.filter(questionnaire=questionnaire):
                response_data = {
                    'id': response.id,
                    'user': response.user.username if response.user else 'Anonyme',
                    'submitted_at': response.submitted_at,
                    'question_responses': []
                }
                
                for qr in QuestionResponse.objects.filter(questionnaire_response=response):
                    response_data['question_responses'].append({
                        'question_id': qr.question.id,
                        'answer': qr.answer_data
                    })
                
                questionnaire_data['responses'].append(response_data)
            
            return Response(questionnaire_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'export: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def questionnaire_duplicate(request, pk):
    """
    API endpoint pour dupliquer un questionnaire
    """
    try:
        original_questionnaire = get_object_or_404(Questionnaire, id=pk)
        
        # Créer une copie du questionnaire
        new_questionnaire = Questionnaire.objects.create(
            title=f"{original_questionnaire.title} (Copie)",
            description=original_questionnaire.description,
            type=original_questionnaire.type,
            status='draft',  # Toujours en brouillon
            is_anonymous=original_questionnaire.is_anonymous,
            allow_multiple_responses=original_questionnaire.allow_multiple_responses,
            show_results_after_submission=original_questionnaire.show_results_after_submission,
            target_audience_type=original_questionnaire.target_audience_type,
            target_departments=original_questionnaire.target_departments,
            target_roles=original_questionnaire.target_roles,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Copier les questions
        for question in original_questionnaire.questions.all():
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
                rating_max=question.rating_max,
                rating_labels=question.rating_labels,
                satisfaction_options=question.satisfaction_options,
                validation_rules=question.validation_rules,
                checkbox_text=question.checkbox_text,
                ranking_items=question.ranking_items,
                top_selection_limit=question.top_selection_limit,
                matrix_questions=question.matrix_questions,
                matrix_options=question.matrix_options,
                likert_scale=question.likert_scale
            )
        
        # Sérialiser la réponse
        serializer = QuestionnaireSerializer(new_questionnaire)
        
        return Response({
            'message': 'Questionnaire dupliqué avec succès',
            'questionnaire': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la duplication: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def questionnaire_status_update(request, pk):
    """
    API endpoint pour mettre à jour le statut d'un questionnaire
    """
    try:
        questionnaire = get_object_or_404(Questionnaire, id=pk)
        new_status = request.data.get('status')
        
        if new_status not in [choice[0] for choice in Questionnaire.STATUS_CHOICES]:
            return Response(
                {'error': 'Statut invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = questionnaire.status
        questionnaire.status = new_status
        questionnaire.save()
        
        return Response({
            'message': f'Statut mis à jour de {old_status} vers {new_status}',
            'questionnaire': {
                'id': questionnaire.id,
                'title': questionnaire.title,
                'status': questionnaire.status,
                'status_display': questionnaire.get_status_display()
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la mise à jour du statut: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )