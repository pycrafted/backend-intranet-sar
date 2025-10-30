from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model, login, logout
from django.utils.crypto import get_random_string
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer
)

User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    """API endpoint pour l'inscription d'un nouvel utilisateur"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Inscription réussie',
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """API endpoint pour la connexion d'un utilisateur"""
    permission_classes = (AllowAny,)

    def post(self, request):
        print("=" * 80)
        print("🔐 [LOGIN_BACKEND] === DÉBUT CONNEXION ===")
        print(f"🔍 [LOGIN_BACKEND] Requête de connexion reçue")
        print(f"🔍 [LOGIN_BACKEND] Méthode: {request.method}")
        print(f"🔍 [LOGIN_BACKEND] Headers:", dict(request.headers))
        print(f"🔍 [LOGIN_BACKEND] Cookies reçus:", request.COOKIES)
        print(f"🔍 [LOGIN_BACKEND] Session avant login:", {
            'session_key': request.session.session_key,
            'has_session': request.session.exists(request.session.session_key) if request.session.session_key else False,
            'is_authenticated': request.user.is_authenticated if hasattr(request, 'user') else 'N/A'
        })
        print(f"🔍 [LOGIN_BACKEND] Données: {request.data}")
        
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print(f"✅ [LOGIN_BACKEND] Utilisateur trouvé: {user.email} (ID: {user.id})")
            
            # Recharger l'utilisateur avec les relations pour optimiser
            user = User.objects.select_related('department', 'manager').get(id=user.id)
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"✅ [LOGIN_BACKEND] Login Django appelé")
            print(f"✅ [LOGIN_BACKEND] Utilisateur connecté: {request.user.is_authenticated}")
            print(f"✅ [LOGIN_BACKEND] User ID: {request.user.id}")
            print(f"✅ [LOGIN_BACKEND] User email: {request.user.email}")
            
            # Vérifier la session après login
            print(f"🍪 [LOGIN_BACKEND] Session après login:", {
                'session_key': request.session.session_key,
                'has_session': request.session.exists(request.session.session_key) if request.session.session_key else False,
                'session_data_keys': list(request.session.keys()) if hasattr(request.session, 'keys') else 'N/A'
            })
            
            # Vérifier les cookies qui seront envoyés
            response = Response({
                'message': 'Connexion réussie',
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
            
            print(f"🍪 [LOGIN_BACKEND] Cookies dans la réponse:", {
                'sessionid_set': 'sessionid' in response.cookies,
                'sessionid_value': response.cookies.get('sessionid').value if 'sessionid' in response.cookies else 'N/A',
                'csrftoken_set': 'csrftoken' in response.cookies,
            })
            print("=" * 80)
            
            return response
        else:
            print(f"❌ [LOGIN_BACKEND] Erreurs de validation: {serializer.errors}")
            print("=" * 80)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """API endpoint pour la déconnexion d'un utilisateur"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print("=" * 80)
        print("🚪 [LOGOUT_BACKEND] === DÉBUT DÉCONNEXION ===")
        print(f"🔍 [LOGOUT_BACKEND] Cookies avant logout:", request.COOKIES)
        print(f"🔍 [LOGOUT_BACKEND] Session avant logout:", {
            'session_key': request.session.session_key,
            'is_authenticated': request.user.is_authenticated
        })
        
        logout(request)
        
        print(f"✅ [LOGOUT_BACKEND] Logout Django appelé")
        print(f"🍪 [LOGOUT_BACKEND] Session après logout:", {
            'session_key': request.session.session_key,
            'has_session': request.session.exists(request.session.session_key) if request.session.session_key else False
        })
        print("=" * 80)
        
        response = Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
        # S'assurer que le cookie de session est supprimé
        response.delete_cookie('sessionid', domain=None)
        print(f"🍪 [LOGOUT_BACKEND] Cookie sessionid supprimé de la réponse")
        return response


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """API endpoint pour récupérer et mettre à jour le profil de l'utilisateur actuel"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Utilisateur non authentifié")
        # Optimiser les requêtes en chargeant les relations
        return User.objects.select_related('department', 'manager').get(id=self.request.user.id)

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserProfileSerializer
        return UserSerializer
    
    def get(self, request, *args, **kwargs):
        print("=" * 80)
        print("👤 [CURRENT_USER_BACKEND] === DÉBUT VÉRIFICATION ===")
        print(f"🔍 [CURRENT_USER_BACKEND] Méthode: {request.method}")
        print(f"🔍 [CURRENT_USER_BACKEND] Cookies reçus:", request.COOKIES)
        print(f"🔍 [CURRENT_USER_BACKEND] Headers:", {
            'origin': request.headers.get('Origin'),
            'referer': request.headers.get('Referer'),
            'host': request.headers.get('Host')
        })
        
        # Vérifier la session
        session_key = request.session.session_key
        print(f"🍪 [CURRENT_USER_BACKEND] Session:", {
            'session_key': session_key,
            'has_session_key': bool(session_key),
            'session_exists': request.session.exists(session_key) if session_key else False,
            'session_keys': list(request.session.keys()) if session_key else []
        })
        
        # Vérifier l'authentification
        is_authenticated = request.user.is_authenticated
        print(f"🔐 [CURRENT_USER_BACKEND] Authentification:", {
            'is_authenticated': is_authenticated,
            'user_id': request.user.id if is_authenticated else 'N/A',
            'user_email': request.user.email if is_authenticated else 'N/A',
            'user_username': request.user.username if is_authenticated else 'N/A'
        })
        
        if not is_authenticated:
            print(f"❌ [CURRENT_USER_BACKEND] Utilisateur NON authentifié - retour 401")
            print(f"🍪 [CURRENT_USER_BACKEND] Raison possible: Session invalide ou expirée")
            print("=" * 80)
            return Response({
                'error': 'Non authentifié',
                'message': 'Aucun utilisateur connecté'
            }, status=401)
        
        # Optimiser les requêtes en chargeant les relations
        user = User.objects.select_related('department', 'manager').get(id=request.user.id)
        
        # get_serializer inclut automatiquement le contexte de la requête
        serializer = self.get_serializer(user)
        user_data = serializer.data
        
        print(f"✅ [CURRENT_USER_BACKEND] Utilisateur trouvé:", {
            'id': user_data.get('id'),
            'email': user_data.get('email'),
            'has_manager': bool(user_data.get('manager')),
            'has_department': bool(user_data.get('department'))
        })
        print("=" * 80)
        
        response = Response(user_data)
        print(f"🍪 [CURRENT_USER_BACKEND] Cookies dans la réponse:", {
            'sessionid_set': 'sessionid' in response.cookies,
            'sessionid_value_length': len(response.cookies.get('sessionid').value) if 'sessionid' in response.cookies else 0
        })
        
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """API endpoint pour récupérer le token CSRF"""
    from django.middleware.csrf import get_token
    token = get_token(request)
    return Response({'csrfToken': token})


class UserListView(generics.ListAPIView):
    """API endpoint pour récupérer la liste des utilisateurs"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Désactiver la pagination pour retourner tous les utilisateurs

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    def list(self, request, *args, **kwargs):
        print("=" * 80)
        print("👥 [USER_LIST_BACKEND] === RÉCUPÉRATION LISTE UTILISATEURS ===")
        queryset = self.get_queryset()
        print(f"👥 [USER_LIST_BACKEND] Nombre d'utilisateurs: {queryset.count()}")
        
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        print(f"👥 [USER_LIST_BACKEND] Type de données: {type(data)}")
        print(f"👥 [USER_LIST_BACKEND] Nombre d'éléments: {len(data) if isinstance(data, list) else 'N/A'}")
        print("=" * 80)
        
        return Response(data)


class AdminUserListView(generics.ListAPIView):
    """Liste complète des utilisateurs (admin uniquement)"""
    queryset = User.objects.all().select_related('department', 'manager')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Récupérer/mettre à jour/supprimer un utilisateur (admin uniquement)"""
    queryset = User.objects.all().select_related('department', 'manager')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class AdminUserGroupsView(APIView):
    """Mettre à jour les groupes d'un utilisateur (admin uniquement)"""
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, user_id: int):
        group_names = request.data.get('groups', [])
        if not isinstance(group_names, list):
            return Response({'detail': 'Format invalide pour groups'}, status=400)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=404)

        groups = list(Group.objects.filter(name__in=group_names))
        user.groups.set(groups)
        user.save()
        return Response({'message': 'Groupes mis à jour', 'groups': [g.name for g in user.groups.all()]})


class AdminUserResetPasswordView(APIView):
    """Réinitialiser le mot de passe d'un utilisateur (admin uniquement)"""
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=404)

        temp_password = get_random_string(length=12)
        user.set_password(temp_password)
        user.save()
        return Response({'message': 'Mot de passe réinitialisé', 'temporary_password': temp_password})

