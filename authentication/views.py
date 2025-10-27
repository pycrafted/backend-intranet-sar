from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model, login, logout
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
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """API endpoint pour la connexion d'un utilisateur"""
    permission_classes = (AllowAny,)

    def post(self, request):
        print(f"🔍 [LOGIN] Requête de connexion reçue")
        print(f"🔍 [LOGIN] Données: {request.data}")
        
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print(f"✅ [LOGIN] Utilisateur trouvé: {user.email}")
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"✅ [LOGIN] Utilisateur connecté: {request.user.is_authenticated}")
            
            return Response({
                'message': 'Connexion réussie',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """API endpoint pour la déconnexion d'un utilisateur"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """API endpoint pour récupérer et mettre à jour le profil de l'utilisateur actuel"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Utilisateur non authentifié")
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserProfileSerializer
        return UserSerializer
    
    def get(self, request, *args, **kwargs):
        print(f"🔍 [CURRENT_USER] Utilisateur authentifié: {request.user.is_authenticated}")
        
        if not request.user.is_authenticated:
            return Response({
                'error': 'Non authentifié',
                'message': 'Aucun utilisateur connecté'
            }, status=401)
        
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


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

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('last_name', 'first_name')

