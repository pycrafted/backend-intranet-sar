"""
Vues de santé du système.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
@permission_classes([])
def health_check(request):
    """
    Endpoint de santé simple.
    """
    return Response({
        'status': 'healthy',
        'message': 'Système opérationnel',
        'service': 'SAR Intranet Backend'
    }, status=status.HTTP_200_OK)