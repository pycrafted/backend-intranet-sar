from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.conf import settings
from .models import Direction, Agent
from .serializers import DirectionSerializer, AgentSerializer, AgentListSerializer, AgentTreeSerializer


class DirectionListView(generics.ListAPIView):
    """Vue pour lister toutes les directions"""
    
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]


class AgentListView(generics.ListAPIView):
    """Vue pour lister tous les agents avec filtres"""
    
    serializer_class = AgentListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Agent.objects.select_related('manager').prefetch_related('directions').all()
        
        # Filtre par direction
        direction_name = self.request.query_params.get('direction', None)
        if direction_name:
            queryset = queryset.filter(directions__name=direction_name)
        
        # Recherche textuelle
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(job_title__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.distinct()


class AgentDetailView(generics.RetrieveAPIView):
    """Vue pour le détail d'un agent"""
    
    queryset = Agent.objects.select_related('manager').prefetch_related('directions')
    serializer_class = AgentSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_tree_view(request):
    """Vue pour l'arborescence complète de l'organigramme"""
    
    # Trouver le CEO (agent sans manager)
    ceo = Agent.objects.filter(manager__isnull=True).select_related('manager').prefetch_related('directions').first()
    
    if not ceo:
        return Response(
            {"error": "Aucun CEO trouvé (agent sans manager)"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = AgentTreeSerializer(ceo, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_search_view(request):
    """Vue pour la recherche avancée d'agents"""
    
    queryset = Agent.objects.select_related('manager').prefetch_related('directions').all()
    
    # Filtre par direction
    direction_name = request.query_params.get('direction', None)
    if direction_name:
        queryset = queryset.filter(directions__name=direction_name)
    
    # Recherche textuelle
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(job_title__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filtre par manager
    manager_id = request.query_params.get('manager', None)
    if manager_id:
        queryset = queryset.filter(manager_id=manager_id)
    
    serializer = AgentListSerializer(queryset.distinct(), many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_subordinates_view(request, agent_id):
    """Vue pour récupérer les subordonnés d'un agent"""
    
    try:
        agent = Agent.objects.get(id=agent_id)
        subordinates = agent.subordinates.select_related('manager').prefetch_related('directions').all()
        serializer = AgentListSerializer(subordinates, many=True, context={'request': request})
        return Response(serializer.data)
    except Agent.DoesNotExist:
        return Response(
            {"error": "Agent non trouvé"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def direction_agents_view(request, direction_name):
    """Vue pour récupérer tous les agents d'une direction spécifique"""
    
    try:
        direction = Direction.objects.get(name=direction_name)
        agents = direction.agents.select_related('manager').prefetch_related('directions').all()
        serializer = AgentListSerializer(agents, many=True, context={'request': request})
        return Response(serializer.data)
    except Direction.DoesNotExist:
        return Response(
            {"error": "Direction non trouvée"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def upload_agent_avatar(request, agent_id):
    """Endpoint pour uploader l'avatar d'un agent"""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        return Response(
            {"error": "Agent non trouvé"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if 'avatar' not in request.FILES:
        return Response(
            {"error": "Aucun fichier avatar fourni"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    avatar_file = request.FILES['avatar']
    
    # Vérifier le type de fichier
    if not avatar_file.content_type.startswith('image/'):
        return Response(
            {"error": "Le fichier doit être une image"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier la taille (max 5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response(
            {"error": "La taille du fichier ne doit pas dépasser 5MB"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Supprimer l'ancien avatar s'il existe
    if agent.avatar:
        try:
            agent.avatar.delete(save=False)
        except:
            pass  # Ignorer les erreurs de suppression
    
    # Sauvegarder le nouvel avatar
    agent.avatar = avatar_file
    agent.save()
    
    # Retourner l'URL de l'avatar
    avatar_url = f"{settings.MEDIA_URL}{agent.avatar}"
    
    return Response({
        "message": "Avatar uploadé avec succès",
        "avatar_url": avatar_url
    }, status=status.HTTP_200_OK)