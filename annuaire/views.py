from rest_framework import generics, status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from .models import Department, Position, Employee, OrganizationalChart
from .serializers import (
    DepartmentSerializer, PositionSerializer, EmployeeListSerializer,
    EmployeeDetailSerializer, EmployeeHierarchySerializer,
    DepartmentHierarchySerializer, OrganizationalChartSerializer,
    UserAnnuaireSerializer
)

User = get_user_model()


class DepartmentListCreateView(generics.ListCreateAPIView):
    """Liste et création des départements"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un département"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class PositionListCreateView(generics.ListCreateAPIView):
    """Liste et création des postes"""
    queryset = Position.objects.select_related('department').all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'level', 'is_management']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'level']
    ordering = ['level', 'title']


class PositionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un poste"""
    queryset = Position.objects.select_related('department').all()
    serializer_class = PositionSerializer


class EmployeeListCreateView(generics.ListCreateAPIView):
    """Liste et création des employés"""
    queryset = Employee.objects.select_related('position', 'position__department', 'manager').filter(is_active=True)
    serializer_class = EmployeeListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['position__department', 'position__level', 'is_active', 'work_schedule']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id', 'position__title']
    ordering_fields = ['last_name', 'first_name', 'hire_date', 'position__level']
    ordering = ['last_name', 'first_name']


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un employé"""
    queryset = Employee.objects.select_related('position', 'position__department', 'manager').all()
    serializer_class = EmployeeDetailSerializer


class OrganizationalChartView(generics.ListCreateAPIView):
    """Liste et création des organigrammes"""
    queryset = OrganizationalChart.objects.filter(is_active=True)
    serializer_class = OrganizationalChartSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']


@api_view(['GET'])
def org_chart_hierarchy(request):
    """Retourne l'organigramme hiérarchique complet"""
    # Trouver le CEO (employé sans manager)
    ceo = Employee.objects.filter(
        manager__isnull=True,
        is_active=True
    ).select_related('position', 'position__department').first()
    
    if not ceo:
        return Response(
            {'error': 'Aucun directeur général trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = EmployeeHierarchySerializer(ceo)
    return Response(serializer.data)


@api_view(['GET'])
def org_chart_by_department(request):
    """Retourne l'organigramme organisé par département"""
    departments = Department.objects.prefetch_related(
        'positions__employees'
    ).all()
    
    serializer = DepartmentHierarchySerializer(departments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def employee_search(request):
    """Recherche avancée d'employés"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    level = request.GET.get('level', '')
    is_manager = request.GET.get('is_manager', '')
    
    queryset = Employee.objects.select_related(
        'position', 'position__department', 'manager'
    ).filter(is_active=True)
    
    if query:
        queryset = queryset.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(position__title__icontains=query)
        )
    
    if department:
        queryset = queryset.filter(position__department__id=department)
    
    if level:
        queryset = queryset.filter(position__level=level)
    
    if is_manager.lower() == 'true':
        queryset = queryset.filter(subordinates__isnull=False).distinct()
    elif is_manager.lower() == 'false':
        queryset = queryset.filter(subordinates__isnull=True)
    
    serializer = EmployeeListSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def employee_subordinates(request, employee_id):
    """Retourne tous les subordonnés d'un employé"""
    try:
        employee = Employee.objects.get(id=employee_id, is_active=True)
        subordinates = employee.get_all_subordinates()
        serializer = EmployeeListSerializer(subordinates, many=True)
        return Response(serializer.data)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employé non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def employee_management_chain(request, employee_id):
    """Retourne la chaîne de management d'un employé"""
    try:
        employee = Employee.objects.get(id=employee_id, is_active=True)
        management_chain = employee.get_management_chain()
        serializer = EmployeeListSerializer(management_chain, many=True)
        return Response(serializer.data)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employé non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def department_statistics(request):
    """Retourne les statistiques par département"""
    stats = Department.objects.annotate(
        total_employees=Count('positions__employees', filter=Q(positions__employees__is_active=True)),
        managers_count=Count('positions__employees', filter=Q(
            positions__employees__is_active=True,
            positions__employees__subordinates__isnull=False
        )),
        positions_count=Count('positions')
    ).values(
        'id', 'name', 'total_employees', 'managers_count', 'positions_count'
    )
    
    return Response(list(stats))


@api_view(['GET'])
def org_chart_data(request):
    """Retourne les données formatées pour l'organigramme frontend"""
    # Structure similaire à celle utilisée dans le frontend
    employees = Employee.objects.select_related(
        'position', 'position__department', 'manager'
    ).filter(is_active=True)
    
    # Grouper par niveau hiérarchique
    hierarchy_data = {}
    for employee in employees:
        level = employee.hierarchy_level
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position.title,
            'department': employee.position.department.name,
            'email': employee.email,
            'phone': employee.phone,
            'location': employee.office_location or employee.position.department.location,
            'avatar': employee.avatar.url if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': employee.manager.id if employee.manager else None,
            'children': []
        })
    
    return Response(hierarchy_data)


# ===== NOUVELLES VUES POUR ORGANIGRAMME/ANNUAIRE CORRIGÉES =====

@api_view(['GET'])
def department_list_for_annuaire(request):
    """
    Liste des départements uniques des employés actifs
    Utilise les modèles annuaire (Department, Position, Employee)
    """
    departments = Department.objects.filter(
        positions__employees__is_active=True
    ).distinct().values_list('name', flat=True).order_by('name')
    
    return Response(list(departments))


@api_view(['GET'])
def employee_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les modèles annuaire (Employee, Department, Position)
    """
    employees = Employee.objects.select_related(
        'position', 'position__department', 'manager'
    ).filter(is_active=True)
    
    hierarchy_data = {}
    
    for employee in employees:
        level = employee.hierarchy_level
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position.title,
            'department': employee.position.department.name,
            'email': employee.email,
            'phone': employee.phone,
            'location': employee.office_location or employee.position.department.location,
            'avatar': employee.avatar.url if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': employee.manager.id if employee.manager else None,
            'children': []
        })
    
    return Response(hierarchy_data)


# ===== NOUVELLES VUES OPTIMISÉES POUR L'ANNUAIRE =====

class AnnuaireUserListView(generics.ListAPIView):
    """
    Vue optimisée pour l'annuaire utilisant les données de l'app authentication
    Retourne tous les utilisateurs actifs avec leurs informations complètes
    """
    serializer_class = UserAnnuaireSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'matricule', 'position', 'department']
    filterset_fields = ['department', 'is_staff', 'is_superuser', 'is_active']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """Retourne tous les utilisateurs actifs avec leurs relations"""
        return User.objects.select_related('manager').filter(
            is_active=True
        ).prefetch_related('subordinates')


@api_view(['GET'])
def annuaire_user_search(request):
    """
    Recherche avancée d'utilisateurs pour l'annuaire
    Utilise les données de l'app authentication
    """
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    is_manager = request.GET.get('is_manager', '')
    
    queryset = User.objects.select_related('manager').filter(is_active=True)
    
    # Recherche textuelle
    if query:
        queryset = queryset.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(matricule__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query)
        )
    
    # Filtre par département
    if department and department != 'Tous':
        queryset = queryset.filter(department=department)
    
    # Filtre par statut manager
    if is_manager.lower() == 'true':
        queryset = queryset.filter(Q(is_staff=True) | Q(is_superuser=True))
    elif is_manager.lower() == 'false':
        queryset = queryset.filter(is_staff=False, is_superuser=False)
    
    serializer = UserAnnuaireSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def annuaire_user_detail(request, user_id):
    """
    Détail d'un utilisateur pour l'annuaire
    """
    try:
        user = User.objects.select_related('manager').prefetch_related('subordinates').get(
            id=user_id, 
            is_active=True
        )
        serializer = UserAnnuaireSerializer(user, context={'request': request})
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def annuaire_departments_list(request):
    """
    Liste des départements uniques des utilisateurs actifs
    """
    departments = User.objects.filter(
        is_active=True,
        department__isnull=False
    ).values_list('department', flat=True).distinct().order_by('department')
    
    return Response(list(departments))


@api_view(['GET'])
def annuaire_statistics(request):
    """
    Statistiques pour l'annuaire
    """
    total_users = User.objects.filter(is_active=True).count()
    total_managers = User.objects.filter(is_active=True, is_staff=True).count()
    total_superusers = User.objects.filter(is_active=True, is_superuser=True).count()
    
    # Statistiques par département
    department_stats = User.objects.filter(
        is_active=True,
        department__isnull=False
    ).values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return Response({
        'total_users': total_users,
        'total_managers': total_managers,
        'total_superusers': total_superusers,
        'department_stats': list(department_stats)
    })


@api_view(['GET'])
def annuaire_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les données de l'app authentication
    """
    # Utilisateurs avec leurs managers
    users = User.objects.select_related('manager').filter(is_active=True)
    
    hierarchy_data = {}
    
    for user in users:
        level = 1 if user.is_superuser else (2 if user.is_staff else 3)
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': user.id,
            'name': user.get_full_name(),
            'role': user.position or 'Employé',
            'department': user.department or 'Non renseigné',
            'email': user.email,
            'phone': user.phone_number or 'Non renseigné',
            'location': 'Dakar, Sénégal',  # Peut être ajouté au modèle User si nécessaire
            'avatar': user.avatar.url if user.avatar else None,
            'initials': f"{user.first_name[0]}{user.last_name[0]}".upper() if user.first_name and user.last_name else "U",
            'level': level,
            'parentId': user.manager.id if user.manager else None,
            'children': []
        })
    
    return Response(hierarchy_data)


# ===== NOUVELLES VUES POUR ORGANIGRAMME/ANNUAIRE CORRIGÉES =====

@api_view(['GET'])
def department_list_for_annuaire(request):
    """
    Liste des départements uniques des employés actifs
    Utilise les modèles annuaire (Department, Position, Employee)
    """
    departments = Department.objects.filter(
        positions__employees__is_active=True
    ).distinct().values_list('name', flat=True).order_by('name')
    
    return Response(list(departments))


@api_view(['GET'])
def employee_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les modèles annuaire (Employee, Department, Position)
    """
    employees = Employee.objects.select_related(
        'position', 'position__department', 'manager'
    ).filter(is_active=True)
    
    hierarchy_data = {}
    
    for employee in employees:
        level = employee.hierarchy_level
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position.title,
            'department': employee.position.department.name,
            'email': employee.email,
            'phone': employee.phone,
            'location': employee.office_location or employee.position.department.location,
            'avatar': employee.avatar.url if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': employee.manager.id if employee.manager else None,
            'children': []
        })
    
    return Response(hierarchy_data)
