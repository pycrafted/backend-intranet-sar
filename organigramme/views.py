from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.conf import settings
from .models import Direction, Agent
from .serializers import DirectionSerializer, AgentSerializer, AgentListSerializer, AgentTreeSerializer
from .hierarchy_serializers import AgentHierarchySerializer


class DirectionListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des directions"""
    
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]


class DirectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour le détail, la mise à jour et la suppression d'une direction"""
    
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]


class AgentListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des agents avec filtres"""
    
    serializer_class = AgentListSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        queryset = Agent.objects.select_related('manager').prefetch_related('directions').all()
        
        # Filtre par direction
        direction_id = self.request.query_params.get('direction', None)
        if direction_id and direction_id != 'all':
            queryset = queryset.filter(directions__id=direction_id)
        
        # Filtre par manager
        manager_id = self.request.query_params.get('manager', None)
        if manager_id and manager_id != 'all':
            queryset = queryset.filter(manager_id=manager_id)
        
        # Recherche textuelle
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(job_title__icontains=search) |
                Q(email__icontains=search) |
                Q(matricule__icontains=search)
            )
        
        return queryset.distinct()


class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour le détail, la mise à jour et la suppression d'un agent"""
    
    queryset = Agent.objects.select_related('manager').prefetch_related('directions')
    serializer_class = AgentSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]


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


# Vues pour la hiérarchie
@api_view(['GET'])
@permission_classes([AllowAny])
def hierarchy_info_view(request):
    """Retourne les informations de hiérarchie de tous les agents"""
    agents = Agent.objects.all().order_by('hierarchy_level', 'last_name')
    serializer = AgentHierarchySerializer(agents, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_hierarchy_detail_view(request, agent_id):
    """Retourne les informations de hiérarchie d'un agent spécifique"""
    try:
        agent = Agent.objects.get(id=agent_id)
        serializer = AgentHierarchySerializer(agent)
        return Response(serializer.data)
    except Agent.DoesNotExist:
        return Response(
            {"error": "Agent non trouvé"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def hierarchy_tree_view(request):
    """Retourne l'arbre hiérarchique complet"""
    # Trouver tous les DG (agents sans manager)
    dgs = Agent.objects.filter(manager__isnull=True)
    
    def build_tree(agent):
        """Construit récursivement l'arbre hiérarchique"""
        subordinates = agent.subordinates.all().order_by('last_name')
        return {
            'agent': AgentHierarchySerializer(agent).data,
            'subordinates': [build_tree(sub) for sub in subordinates]
        }
    
    tree = [build_tree(dg) for dg in dgs]
    return Response(tree)


@api_view(['POST'])
@permission_classes([AllowAny])
def rebuild_hierarchy_view(request):
    """Reconstruit tous les niveaux hiérarchiques"""
    try:
        Agent.rebuild_hierarchy_levels()
        return Response({
            "message": "Hiérarchie reconstruite avec succès",
            "total_agents": Agent.objects.count()
        })
    except Exception as e:
        return Response(
            {"error": f"Erreur lors de la reconstruction: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def hierarchy_stats_view(request):
    """Retourne les statistiques de la hiérarchie"""
    from django.db.models import Count, Max, Min
    
    stats = Agent.objects.aggregate(
        total_agents=Count('id'),
        max_level=Max('hierarchy_level'),
        min_level=Min('hierarchy_level'),
        dg_count=Count('id', filter=Q(manager__isnull=True)),
        managers_count=Count('id', filter=Q(subordinates__isnull=False))
    )
    
    # Compter les agents par niveau
    level_counts = {}
    for agent in Agent.objects.all():
        level = agent.hierarchy_level
        level_counts[level] = level_counts.get(level, 0) + 1
    
    return Response({
        **stats,
        'agents_by_level': level_counts
    })