from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.google.provider import GoogleProvider
import requests
import json
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer
)

User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    """
    API endpoint pour l'inscription d'un nouvel utilisateur
    """
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
    """
    TEMPORAIREMENT : API endpoint désactivé - Mode démo activé
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        # TEMPORAIREMENT : Retourner un utilisateur de démo
        print(f"🔍 [LOGIN] Mode démo activé - Connexion désactivée")
        
        # Créer un utilisateur de démo
        demo_user = {
            'id': 1,
            'username': 'demo',
            'email': 'demo@sar.sn',
            'first_name': 'Utilisateur',
            'last_name': 'Démo',
            'full_name': 'Utilisateur Démo',
            'avatar': '',
            'avatar_url': '',
            'phone_number': '+221 33 123 45 67',
            'office_phone': '+221 33 123 45 68',
            'position': 'Employé',
            'department': 'IT',
            'matricule': 'SAR001',
            'manager': None,
            'manager_info': None,
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
            'last_login': '2025-01-07T17:00:00Z',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-07T17:00:00Z',
            'google_id': None,
            'google_email': None,
            'google_avatar_url': None,
            'is_google_connected': False
        }
        
        return Response({
            'message': 'Mode démo activé - Connexion désactivée',
            'user': demo_user
        }, status=status.HTTP_200_OK)
    
    def _auto_connect_google(self, user, request):
        """
        Tente une connexion Google automatique en arrière-plan
        """
        try:
            print(f"🔍 [AUTO_GOOGLE] Tentative de connexion automatique pour {user.email}")
            
            # Configuration OAuth
            client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
            client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
            redirect_uri = f"{request.scheme}://{request.get_host()}/api/auth/google/callback/"
            
            # Scopes demandés
            scopes = [
                'openid',
                'email',
                'profile',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/calendar.readonly',
            ]
            
            # Construire l'URL d'authentification Google
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={'+'.join(scopes)}&"
                f"response_type=code&"
                f"access_type=offline&"
                f"prompt=consent&"
                f"login_hint={user.email}"
            )
            
            print(f"🔗 [AUTO_GOOGLE] URL d'authentification générée: {auth_url}")
            
            # Stocker l'URL dans la session pour utilisation ultérieure
            request.session['google_auth_url'] = auth_url
            request.session['user_id_for_google_auth'] = user.id
            request.session['auto_google_auth'] = True
            
            print(f"✅ [AUTO_GOOGLE] Session mise à jour pour l'utilisateur {user.id}")
            
            # Retourner l'URL pour que le frontend puisse l'ouvrir automatiquement
            return {
                'success': True,
                'auth_url': auth_url,
                'message': 'URL d\'authentification Google générée'
            }
            
        except Exception as e:
            print(f"❌ [AUTO_GOOGLE] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_google_tokens_for_user(self, user, request):
        """
        Génère automatiquement les tokens Google OAuth pour un utilisateur
        """
        try:
            print(f"🔍 [GOOGLE_AUTH] Génération des tokens pour l'utilisateur: {user.email}")
            print(f"🔍 [GOOGLE_AUTH] Utilisateur ID: {user.id}")
            print(f"🔍 [GOOGLE_AUTH] Utilisateur déjà connecté à Google: {user.is_google_connected()}")
            
            # Configuration OAuth
            client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
            client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
            redirect_uri = f"{request.scheme}://{request.get_host()}/api/auth/google/callback/"
            
            print(f"🔍 [GOOGLE_AUTH] Client ID: {client_id}")
            print(f"🔍 [GOOGLE_AUTH] Redirect URI: {redirect_uri}")
            
            # Scopes demandés
            scopes = [
                'openid',
                'email',
                'profile',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/calendar.readonly',
            ]
            
            # Construire l'URL d'authentification Google
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={'+'.join(scopes)}&"
                f"response_type=code&"
                f"access_type=offline&"
                f"prompt=consent&"
                f"login_hint={user.email}"  # Suggérer l'email de l'utilisateur
            )
            
            print(f"🔗 [GOOGLE_AUTH] URL d'authentification Google générée: {auth_url}")
            
            # Stocker l'URL d'authentification dans la session pour utilisation ultérieure
            request.session['google_auth_url'] = auth_url
            request.session['user_id_for_google_auth'] = user.id
            
            print(f"✅ [GOOGLE_AUTH] Session mise à jour pour l'utilisateur {user.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ [GOOGLE_AUTH] Erreur lors de la génération des tokens Google: {e}")
            import traceback
            traceback.print_exc()
            return False


class UserLogoutView(APIView):
    """
    API endpoint pour la déconnexion d'un utilisateur
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        logout(request)
        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    TEMPORAIREMENT : API endpoint désactivé - Mode démo activé
    """
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get_object(self):
        # TEMPORAIREMENT : Retourner un utilisateur de démo
        demo_user = {
            'id': 1,
            'username': 'demo',
            'email': 'demo@sar.sn',
            'first_name': 'Utilisateur',
            'last_name': 'Démo',
            'full_name': 'Utilisateur Démo',
            'avatar': '',
            'avatar_url': '',
            'phone_number': '+221 33 123 45 67',
            'office_phone': '+221 33 123 45 68',
            'position': 'Employé',
            'department': 'IT',
            'matricule': 'SAR001',
            'manager': None,
            'manager_info': None,
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
            'last_login': '2025-01-07T17:00:00Z',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-07T17:00:00Z',
            'google_id': None,
            'google_email': None,
            'google_avatar_url': None,
            'is_google_connected': False
        }
        return demo_user

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserProfileSerializer
        return UserSerializer
    
    def get(self, request, *args, **kwargs):
        """
        Récupérer les informations de l'utilisateur actuel
        """
        print(f"🔍 [CURRENT_USER] Requête reçue - Méthode: {request.method}")
        print(f"🔍 [CURRENT_USER] Headers: {dict(request.headers)}")
        print(f"🔍 [CURRENT_USER] Utilisateur authentifié: {request.user.is_authenticated}")
        print(f"🔍 [CURRENT_USER] Utilisateur: {request.user}")
        print(f"🔍 [CURRENT_USER] Session: {dict(request.session)}")
        
        if not request.user.is_authenticated:
            print("❌ [CURRENT_USER] Utilisateur non authentifié")
            return Response({
                'error': 'Non authentifié',
                'message': 'Aucun utilisateur connecté'
            }, status=401)
        
        print(f"✅ [CURRENT_USER] Utilisateur authentifié: {request.user.email}")
        serializer = self.get_serializer(request.user)
        print(f"✅ [CURRENT_USER] Données sérialisées: {serializer.data}")
        return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    """
    API endpoint pour uploader un avatar
    """
    if 'avatar' not in request.FILES:
        return Response({'error': 'Aucun fichier avatar fourni'}, status=status.HTTP_400_BAD_REQUEST)
    
    avatar_file = request.FILES['avatar']
    
    # Validation du fichier
    if avatar_file.size > 5 * 1024 * 1024:  # 5MB max
        return Response({'error': 'Le fichier est trop volumineux (max 5MB)'}, status=status.HTTP_400_BAD_REQUEST)
    
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return Response({'error': 'Type de fichier non supporté'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Sauvegarder l'avatar
    user = request.user
    user.avatar = avatar_file
    user.save()
    
    return Response({
        'message': 'Avatar uploadé avec succès',
        'avatar_url': user.avatar.url if user.avatar else None
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth_status(request):
    """
    API endpoint pour vérifier le statut d'authentification
    """
    return Response({
        'authenticated': True,
        'user_id': request.user.id,
        'username': request.user.username,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser
    })


class UserListView(generics.ListAPIView):
    """
    API endpoint pour récupérer la liste des utilisateurs
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retourne tous les utilisateurs actifs, triés par nom
        """
        return User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    def list(self, request, *args, **kwargs):
        """
        Override pour ajouter des logs de débogage
        """
        print(f"🔍 UserListView - Utilisateur authentifié: {request.user}")
        print(f"🔍 UserListView - Headers: {dict(request.headers)}")
        
        try:
            queryset = self.get_queryset()
            print(f"🔍 UserListView - Nombre d'utilisateurs trouvés: {queryset.count()}")
            
            serializer = self.get_serializer(queryset, many=True)
            print(f"🔍 UserListView - Données sérialisées: {serializer.data}")
            
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ UserListView - Erreur: {e}")
            return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """
    API endpoint pour récupérer le token CSRF
    """
    print(f"🔍 [CSRF] Requête CSRF reçue")
    print(f"🔍 [CSRF] Headers: {dict(request.headers)}")
    print(f"🔍 [CSRF] Session: {dict(request.session)}")
    
    from django.middleware.csrf import get_token
    token = get_token(request)
    print(f"✅ [CSRF] Token généré: {token[:20]}...")
    
    return Response({'csrfToken': token})


# ===== ENDPOINTS OAUTH 2.0 GOOGLE =====

@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_url(request):
    """
    API endpoint pour obtenir l'URL d'authentification Google
    """
    try:
        # Configuration OAuth Google
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        redirect_uri = f"{request.scheme}://{request.get_host()}/api/auth/google/callback/"
        
        # Scopes demandés
        scopes = [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
        ]
        
        # Construire l'URL d'authentification Google
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={'+'.join(scopes)}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        return Response({
            'auth_url': auth_url,
            'client_id': client_id,
            'redirect_uri': redirect_uri
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la génération de l\'URL d\'authentification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def google_auth_callback(request):
    """
    API endpoint pour traiter le callback d'authentification Google
    """
    try:
        # Gérer les requêtes GET et POST
        if request.method == 'GET':
            code = request.GET.get('code')
        else:
            code = request.data.get('code')
            
        print(f"🔍 [GOOGLE_CALLBACK] Méthode: {request.method}")
        print(f"🔍 [GOOGLE_CALLBACK] Code reçu: {code}")
        print(f"🔍 [GOOGLE_CALLBACK] Paramètres GET: {dict(request.GET)}")
        print(f"🔍 [GOOGLE_CALLBACK] Paramètres POST: {request.data}")
        
        if not code:
            return Response({
                'error': 'Code d\'autorisation manquant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Configuration OAuth
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        redirect_uri = f"{request.scheme}://{request.get_host()}/api/auth/google/callback/"
        
        # Échanger le code contre un token d'accès
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            return Response({
                'error': f'Erreur OAuth: {token_json.get("error_description", "Erreur inconnue")}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        
        # Récupérer les informations utilisateur depuis Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_data = user_response.json()
        
        if 'error' in user_data:
            return Response({
                'error': f'Erreur lors de la récupération des données utilisateur: {user_data.get("error")}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer ou récupérer l'utilisateur
        google_id = user_data.get('id')
        email = user_data.get('email')
        first_name = user_data.get('given_name', '')
        last_name = user_data.get('family_name', '')
        avatar_url = user_data.get('picture', '')
        
        # Chercher un utilisateur existant avec cet email ou cet ID Google
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(google_id=google_id)
            except User.DoesNotExist:
                # Créer un nouvel utilisateur
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    google_id=google_id,
                    google_email=email,
                    google_avatar_url=avatar_url,
                    google_access_token=access_token,
                    google_refresh_token=refresh_token,
                )
        
        # Mettre à jour les informations Google
        user.google_id = google_id
        user.google_email = email
        user.google_avatar_url = avatar_url
        user.google_access_token = access_token
        user.google_refresh_token = refresh_token
        user.save()
        
        # Connecter l'utilisateur avec le backend approprié
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        print(f"✅ [GOOGLE_CALLBACK] Utilisateur connecté: {user.email}")
        print(f"✅ [GOOGLE_CALLBACK] Google ID: {google_id}")
        print(f"✅ [GOOGLE_CALLBACK] Google Email: {email}")
        
        # Pour les requêtes GET (redirection depuis Google), rediriger vers le frontend
        if request.method == 'GET':
            from django.shortcuts import redirect
            return redirect('http://localhost:3000/accueil?google_auth=success')
        
        # Pour les requêtes POST (API), retourner JSON
        return Response({
            'message': 'Authentification Google réussie',
            'user': UserSerializer(user).data,
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de l\'authentification Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def google_disconnect(request):
    """
    API endpoint pour déconnecter le compte Google
    """
    try:
        user = request.user
        user.google_id = None
        user.google_email = None
        user.google_avatar_url = None
        user.google_access_token = None
        user.google_refresh_token = None
        user.google_token_expires_at = None
        user.save()
        
        return Response({
            'message': 'Compte Google déconnecté avec succès'
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la déconnexion Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_status(request):
    """
    API endpoint pour vérifier le statut de connexion Google
    """
    try:
        user = request.user
        is_connected = user.is_google_connected()
        
        return Response({
            'is_google_connected': is_connected,
            'google_email': user.google_email if is_connected else None,
            'google_avatar_url': user.google_avatar_url if is_connected else None,
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la vérification du statut Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_google_auth_url(request):
    """
    API endpoint pour récupérer l'URL d'authentification Google pour l'utilisateur connecté
    """
    try:
        user = request.user
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Utilisateur connecté: {user.email}")
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Utilisateur ID: {user.id}")
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Headers: {dict(request.headers)}")
        
        # Vérifier si l'utilisateur a déjà des tokens Google
        is_google_connected = user.is_google_connected()
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Utilisateur déjà connecté à Google: {is_google_connected}")
        
        if is_google_connected:
            print(f"✅ [GET_GOOGLE_AUTH_URL] Utilisateur déjà connecté à Google avec l'email: {user.google_email}")
            return Response({
                'message': 'Utilisateur déjà connecté à Google',
                'is_google_connected': True,
                'google_email': user.google_email
            })
        
        # Configuration OAuth
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        redirect_uri = f"{request.scheme}://{request.get_host()}/api/auth/google/callback/"
        
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Client ID: {client_id}")
        print(f"🔍 [GET_GOOGLE_AUTH_URL] Redirect URI: {redirect_uri}")
        
        # Scopes demandés
        scopes = [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
        ]
        
        # Construire l'URL d'authentification Google
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={'+'.join(scopes)}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"login_hint={user.email}"  # Suggérer l'email de l'utilisateur
        )
        
        print(f"🔗 [GET_GOOGLE_AUTH_URL] URL d'authentification Google générée: {auth_url}")
        
        # Stocker l'ID utilisateur dans la session pour le callback
        request.session['user_id_for_google_auth'] = user.id
        print(f"✅ [GET_GOOGLE_AUTH_URL] Session mise à jour pour l'utilisateur {user.id}")
        
        return Response({
            'auth_url': auth_url,
            'message': 'URL d\'authentification Google générée',
            'is_google_connected': False
        })
        
    except Exception as e:
        print(f"❌ [GET_GOOGLE_AUTH_URL] Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Erreur lors de la génération de l\'URL d\'authentification Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
