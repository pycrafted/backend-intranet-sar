from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import SecurityDocument
from .serializers import SecurityDocumentSerializer, SecurityDocumentUploadSerializer

class SecurityDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les documents de sécurité
    """
    queryset = SecurityDocument.objects.filter(is_active=True)
    permission_classes = [AllowAny]  # Accessible à tous (comme les documents)
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return SecurityDocumentUploadSerializer
        return SecurityDocumentSerializer
    
    def get_queryset(self):
        """Retourne les documents actifs, triés par ordre puis date"""
        return SecurityDocument.objects.filter(is_active=True).order_by('order', '-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        Liste tous les documents de sécurité actifs
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Récupère un document spécifique
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Crée un nouveau document de sécurité
        """
        serializer = SecurityDocumentUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Calculer la taille du fichier
            file = serializer.validated_data['file']
            file_size = file.size
            
            # Créer le document avec l'utilisateur connecté (ou un utilisateur par défaut si non authentifié)
            uploaded_by = request.user if request.user.is_authenticated else None
            
            # Si aucun utilisateur n'est connecté, utiliser le premier superuser disponible
            if uploaded_by is None:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                superuser = User.objects.filter(is_superuser=True).first()
                uploaded_by = superuser
            
            # Si toujours aucun utilisateur, créer un utilisateur système par défaut
            if uploaded_by is None:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                uploaded_by, _ = User.objects.get_or_create(
                    username='system',
                    defaults={
                        'email': 'system@sar.sn',
                        'first_name': 'Système',
                        'last_name': 'SAR',
                    }
                )
            
            document = serializer.save(
                uploaded_by=uploaded_by,
                file_size=file_size
            )
            
            # Retourner le document avec le serializer de lecture
            read_serializer = SecurityDocumentSerializer(document, context={'request': request})
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """
        Met à jour un document existant
        """
        instance = self.get_object()
        serializer = SecurityDocumentUploadSerializer(
            instance, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Si un nouveau fichier est fourni, mettre à jour la taille
            if 'file' in serializer.validated_data:
                file = serializer.validated_data['file']
                serializer.validated_data['file_size'] = file.size
            
            document = serializer.save()
            
            # Retourner le document avec le serializer de lecture
            read_serializer = SecurityDocumentSerializer(document, context={'request': request})
            return Response(read_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un document (soft delete en mettant is_active=False)
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
