from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .services import mai_service
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def search_question(request):
    """
    Recherche une réponse à une question dans le dataset SAR officiel.
    """
    try:
        data = request.data
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return Response({
                'success': False,
                'error': 'Question requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si la question concerne la SAR
        if not mai_service.is_question_about_sar(user_question):
            return Response({
                'success': False,
                'error': 'Cette question ne concerne pas la SAR. Je ne peux répondre qu\'aux questions sur la Société Africaine de Raffinage basées sur notre dataset officiel.',
                'suggestion': 'Posez une question sur la SAR, ses activités, son histoire, ses produits, etc.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Rechercher la réponse
        result = mai_service.search_answer(user_question, threshold=0.3)
        
        if result:
            return Response({
                'success': True,
                'question': result['question'],
                'answer': result['answer'],
                'similarity': result['similarity'],
                'source': 'Dataset officiel SAR'
            })
        else:
            # Si aucune correspondance exacte, fournir le contexte disponible
            context = mai_service.get_context_for_question(user_question)
            return Response({
                'success': False,
                'error': 'Aucune réponse exacte trouvée dans le dataset SAR.',
                'context': context,
                'suggestion': 'Essayez de reformuler votre question ou consultez les questions liées ci-dessus.'
            })
    
    except Exception as e:
        logger.error(f"Erreur lors de la recherche MAI: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_context(request):
    """
    Obtient le contexte pour une question (utilisé par l'IA).
    """
    try:
        question = request.GET.get('question', '').strip()
        
        if not question:
            return Response({
                'success': False,
                'error': 'Question requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si la question concerne la SAR
        if not mai_service.is_question_about_sar(question):
            return Response({
                'success': False,
                'context': '',
                'error': 'Question non liée à la SAR'
            })
        
        # Obtenir le contexte
        context = mai_service.get_context_for_question(question)
        
        return Response({
            'success': True,
            'context': context,
            'question': question
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contexte MAI: {e}")
        return Response({
            'success': False,
            'context': '',
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def get_statistics(request):
    """
    Obtient les statistiques du dataset MAI.
    """
    try:
        stats = {
            'total_questions': mai_service.get_question_count(),
            'dataset_loaded': len(mai_service.qa_pairs) > 0,
            'service_status': 'active'
        }
        
        return Response({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques MAI: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])  # AUTHENTIFICATION DÉSACTIVÉE
def get_sample_questions(request):
    """
    Obtient un échantillon de questions du dataset pour aider l'utilisateur.
    """
    try:
        limit = int(request.GET.get('limit', 10))
        questions = mai_service.get_all_questions()[:limit]
        
        return Response({
            'success': True,
            'questions': questions,
            'total_available': mai_service.get_question_count()
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des questions d'exemple: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
