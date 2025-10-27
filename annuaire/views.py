from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from .models import Department, Employee
from .serializers import (
    DepartmentSerializer, EmployeeListSerializer,
    EmployeeDetailSerializer, EmployeeHierarchySerializer,
    DepartmentHierarchySerializer, UserAnnuaireSerializer
)

User = get_user_model()


class DepartmentListCreateView(generics.ListCreateAPIView):
    """Liste et création des départements"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def list(self, request, *args, **kwargs):
        """Liste des départements avec logs"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DEPARTMENT_LIST] Récupération des départements - IP: {request.META.get('REMOTE_ADDR')}")
        
        try:
            departments = self.get_queryset()
            logger.info(f"[DEPARTMENT_LIST] {departments.count()} départements trouvés")
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"[DEPARTMENT_LIST] Erreur: {str(e)}")
            return Response({
                'error': 'Erreur lors de la récupération des départements',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un département"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]


class EmployeeListCreateView(generics.ListCreateAPIView):
    """Liste et création des employés"""
    queryset = Employee.objects.select_related('department')
    serializer_class = EmployeeListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id', 'position_title']
    ordering_fields = ['last_name', 'first_name']
    ordering = ['last_name', 'first_name']
    
    def list(self, request, *args, **kwargs):
        """Liste des employés avec logs pour les avatars"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            employees = self.get_queryset()
            logger.info(f"[EMPLOYEE_LIST] {employees.count()} employés trouvés")
            
            # Logs spécifiques pour les avatars
            logger.info(f"[EMPLOYEE_LIST] === ANALYSE DES AVATARS ===")
            for emp in employees[:3]:  # Logs pour les 3 premiers employés
                logger.info(f"[EMPLOYEE_LIST] {emp.full_name}: {emp.avatar.url if emp.avatar else 'AUCUN'}")
            
            response = super().list(request, *args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"[EMPLOYEE_LIST] Erreur: {str(e)}")
            return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Création d'un employé avec logs détaillés"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[EMPLOYEE_CREATE] Début création employé - IP: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"[EMPLOYEE_CREATE] Données reçues: {request.data}")
        
        try:
            # Validation des données requises
            required_fields = ['first_name', 'last_name', 'email', 'department', 'position_title', 'employee_id']
            missing_fields = [field for field in required_fields if not request.data.get(field)]
            
            if missing_fields:
                logger.error(f"[EMPLOYEE_CREATE] Champs manquants: {missing_fields}")
                return Response({
                    'error': 'Champs manquants',
                    'missing_fields': missing_fields,
                    'required_fields': required_fields
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérification de l'unicité de l'email
            email = request.data.get('email')
            if Employee.objects.filter(email=email).exists():
                logger.error(f"[EMPLOYEE_CREATE] Email déjà existant: {email}")
                return Response({
                    'error': 'Email déjà existant',
                    'field': 'email',
                    'value': email
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérification de l'unicité de l'employee_id
            employee_id = request.data.get('employee_id')
            if Employee.objects.filter(employee_id=employee_id).exists():
                logger.error(f"[EMPLOYEE_CREATE] Matricule déjà existant: {employee_id}")
                return Response({
                    'error': 'Matricule déjà existant',
                    'field': 'employee_id',
                    'value': employee_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérification de l'existence du département
            department_id = request.data.get('department')
            try:
                department = Department.objects.get(id=department_id)
                logger.info(f"[EMPLOYEE_CREATE] Département trouvé: {department.name}")
            except Department.DoesNotExist:
                logger.error(f"[EMPLOYEE_CREATE] Département inexistant: {department_id}")
                return Response({
                    'error': 'Département inexistant',
                    'field': 'department',
                    'value': department_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Logs détaillés pour l'avatar
            logger.info(f"[EMPLOYEE_CREATE] === GESTION DE L'AVATAR ===")
            avatar_file = request.FILES.get('avatar')
            if avatar_file:
                logger.info(f"[EMPLOYEE_CREATE] Avatar reçu:")
                logger.info(f"  - Nom: {avatar_file.name}")
                logger.info(f"  - Taille: {avatar_file.size} bytes")
                logger.info(f"  - Type: {avatar_file.content_type}")
                logger.info(f"  - Type de fichier: {type(avatar_file)}")
            else:
                logger.info(f"[EMPLOYEE_CREATE] Aucun avatar reçu")
            
            # Création de l'employé
            # IMPORTANT: Fusionner request.data et request.FILES
            logger.info(f"[EMPLOYEE_CREATE] === ANALYSE DES DONNÉES ===")
            logger.info(f"[EMPLOYEE_CREATE] request.data: {request.data}")
            logger.info(f"[EMPLOYEE_CREATE] request.FILES: {request.FILES}")
            logger.info(f"[EMPLOYEE_CREATE] Fichiers disponibles: {list(request.FILES.keys())}")
            
            # Fusionner les données et les fichiers
            data = request.data.copy()
            data.update(request.FILES)
            logger.info(f"[EMPLOYEE_CREATE] Données fusionnées: {data}")
            
            serializer = self.get_serializer(data=data)
            logger.info(f"[EMPLOYEE_CREATE] Serializer créé avec données fusionnées")
            
            if serializer.is_valid():
                employee = serializer.save()
                logger.info(f"[EMPLOYEE_CREATE] Employé créé avec succès: {employee.full_name} (ID: {employee.id})")
                
                # Logs pour l'avatar après création
                if employee.avatar:
                    logger.info(f"[EMPLOYEE_CREATE] Avatar sauvegardé:")
                    logger.info(f"  - URL: {employee.avatar.url}")
                    logger.info(f"  - Nom: {employee.avatar.name}")
                    logger.info(f"  - Taille: {employee.avatar.size} bytes")
                    logger.info(f"  - Chemin: {employee.avatar.path}")
                else:
                    logger.info(f"[EMPLOYEE_CREATE] Aucun avatar sauvegardé")
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"[EMPLOYEE_CREATE] Erreurs de validation: {serializer.errors}")
                return Response({
                    'error': 'Erreurs de validation',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"[EMPLOYEE_CREATE] Erreur inattendue: {str(e)}")
            return Response({
                'error': 'Erreur interne du serveur',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un employé"""
    queryset = Employee.objects.select_related('department').all()
    serializer_class = EmployeeDetailSerializer
    permission_classes = [AllowAny]



@api_view(['GET'])
@permission_classes([AllowAny])
def employee_search(request):
    """Recherche avancée d'employés"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    level = request.GET.get('level', '')
    queryset = Employee.objects.select_related(
        'department'
    )
    
    if query:
        queryset = queryset.filter(
            Q(first_name__istartswith=query) |
            Q(last_name__istartswith=query) |
            Q(email__istartswith=query) |
            Q(employee_id__istartswith=query) |
            Q(position_title__istartswith=query) |
            Q(phone_fixed__istartswith=query) |
            Q(phone_mobile__istartswith=query) |
            Q(department__name__istartswith=query)
        )
    
    if department:
        queryset = queryset.filter(department__id=department)
    
    # Le niveau hiérarchique est maintenant calculé dynamiquement
    # if level:
    #     queryset = queryset.filter(position__level=level)
    
    
    serializer = EmployeeListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)






@api_view(['GET'])
@permission_classes([AllowAny])
def department_statistics(request):
    """Retourne les statistiques par département"""
    stats = Department.objects.annotate(
        total_employees=Count('employees')
    ).values(
        'id', 'name', 'total_employees'
    )
    
    return Response(list(stats))




# ===== NOUVELLES VUES POUR ORGANIGRAMME/ANNUAIRE CORRIGÉES =====

@api_view(['GET'])
@permission_classes([AllowAny])
def department_list_for_annuaire(request):
    """
    Liste des départements uniques des employés actifs
    Utilise les modèles annuaire (Department, Position, Employee)
    """
    departments = Department.objects.filter(
    ).distinct().values_list('name', flat=True).order_by('name')
    
    return Response(list(departments))


@api_view(['GET'])
@permission_classes([AllowAny])
def employee_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les modèles annuaire (Employee, Department, Position)
    """
    employees = Employee.objects.select_related(
        'department'
    )
    
    hierarchy_data = {}
    
    for employee in employees:
        # Tous les employés sont au niveau 1 maintenant (pas de hiérarchie)
        level = 1
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position_title,
            'department': employee.department.name,
            'email': employee.email,
            'phone_fixed': employee.phone_fixed,
            'phone_mobile': employee.phone_mobile,
                'location': 'Non spécifié',
            'avatar': request.build_absolute_uri(employee.avatar.url) if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': None,  # Plus de manager
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
    filterset_fields = ['department', 'is_staff', 'is_superuser']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """Retourne tous les utilisateurs actifs avec leurs relations"""
        return User.objects.select_related('manager').filter(
        ).prefetch_related('subordinates')


@api_view(['GET'])
@permission_classes([AllowAny])
def annuaire_user_search(request):
    """
    Recherche avancée d'utilisateurs pour l'annuaire
    Utilise les données de l'app authentication
    """
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    is_manager = request.GET.get('is_manager', '')
    
    queryset = User.objects.select_related('manager')
    
    # Recherche textuelle
    if query:
        queryset = queryset.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(matricule__icontains=query) |
            Q(position_title__icontains=query) |
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
@permission_classes([AllowAny])
def annuaire_user_detail(request, user_id):
    """
    Détail d'un utilisateur pour l'annuaire
    """
    try:
        user = User.objects.select_related('manager').prefetch_related('subordinates').get(
            id=user_id, 
        )
        serializer = UserAnnuaireSerializer(user, context={'request': request})
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def annuaire_departments_list(request):
    """
    Liste des départements uniques des utilisateurs actifs
    """
    departments = User.objects.filter(
        department__isnull=False
    ).values_list('department', flat=True).distinct().order_by('department')
    
    return Response(list(departments))


@api_view(['GET'])
@permission_classes([AllowAny])
def annuaire_statistics(request):
    """
    Statistiques pour l'annuaire
    """
    total_users = User.objects.count()
    total_managers = User.objects.filter(is_staff=True).count()
    total_superusers = User.objects.filter(is_superuser=True).count()
    
    # Statistiques par département
    department_stats = User.objects.filter(
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
@permission_classes([AllowAny])
def annuaire_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les données de l'app annuaire (Employee)
    Compatible avec employee_hierarchy_data
    """
    employees = Employee.objects.select_related(
        'department'
    )
    
    hierarchy_data = {}
    
    for employee in employees:
        # Tous les employés sont au niveau 1 maintenant (pas de hiérarchie)
        level = 1
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position_title,
            'department': employee.department.name,
            'email': employee.email,
            'phone_fixed': employee.phone_fixed,
            'phone_mobile': employee.phone_mobile,
            'location': 'Non spécifié',
            'avatar': request.build_absolute_uri(employee.avatar.url) if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': None,  # Plus de manager
            'children': []
        })
    
    return Response(hierarchy_data)


# ===== NOUVELLES VUES POUR ORGANIGRAMME/ANNUAIRE CORRIGÉES =====

@api_view(['GET'])
@permission_classes([AllowAny])
def department_list_for_annuaire(request):
    """
    Liste des départements uniques des employés actifs
    Utilise les modèles annuaire (Department, Position, Employee)
    """
    departments = Department.objects.filter(
    ).distinct().values_list('name', flat=True).order_by('name')
    
    return Response(list(departments))


@api_view(['GET'])
@permission_classes([AllowAny])
def employee_hierarchy_data(request):
    """
    Données hiérarchiques pour l'organigramme
    Utilise les modèles annuaire (Employee, Department, Position)
    """
    employees = Employee.objects.select_related(
        'department'
    )
    
    hierarchy_data = {}
    
    for employee in employees:
        # Tous les employés sont au niveau 1 maintenant (pas de hiérarchie)
        level = 1
        
        if level not in hierarchy_data:
            hierarchy_data[level] = []
        
        hierarchy_data[level].append({
            'id': employee.id,
            'name': employee.full_name,
            'role': employee.position_title,
            'department': employee.department.name,
            'email': employee.email,
            'phone_fixed': employee.phone_fixed,
            'phone_mobile': employee.phone_mobile,
                'location': 'Non spécifié',
            'avatar': request.build_absolute_uri(employee.avatar.url) if employee.avatar else None,
            'initials': employee.initials,
            'level': level,
            'parentId': None,  # Plus de manager
            'children': []
        })
    
    return Response(hierarchy_data)
