from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services import mai_service
from .loading_messages import loading_service
import logging
import time

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([])
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
        
        # FILTRE SAR SUPPRIMÉ - Toutes les questions sont acceptées
        # Le dataset contient uniquement des questions SAR pertinentes
        
        # Simuler un délai de traitement pour démontrer les messages de chargement
        # En production, ce délai sera naturel
        time.sleep(0.5)
        
        # Rechercher la réponse avec seuil réduit pour plus de flexibilité
        result = mai_service.search_answer(user_question, threshold=0.2)
        
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

@api_view(['POST'])
@permission_classes([])
def get_loading_message(request):
    """
    Génère un message de chargement contextuel basé sur la question.
    """
    try:
        data = request.data
        question = data.get('question', '').strip()
        phase = data.get('phase', 'searching')  # 'searching' ou 'processing'
        
        if not question:
            return Response({
                'success': False,
                'error': 'Question requise pour générer le message de chargement'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Générer le message de chargement contextuel
        loading_message = loading_service.get_loading_message(question, phase)
        
        return Response({
            'success': True,
            'message': loading_message,
            'phase': phase,
            'context': loading_service._detect_context(question.lower())
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération du message de chargement: {e}")
        return Response({
            'success': False,
            'error': 'Erreur lors de la génération du message de chargement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([])
def get_progressive_loading(request):
    """
    Génère une séquence de messages de chargement progressifs.
    """
    try:
        data = request.data
        question = data.get('question', '').strip()
        duration = float(data.get('duration', 2.0))  # Durée en secondes
        
        if not question:
            return Response({
                'success': False,
                'error': 'Question requise pour générer les messages de chargement'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Générer la séquence de messages progressifs
        messages = loading_service.get_progressive_messages(question, duration)
        
        return Response({
            'success': True,
            'messages': messages,
            'total_duration': duration,
            'message_count': len(messages)
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération des messages progressifs: {e}")
        return Response({
            'success': False,
            'error': 'Erreur lors de la génération des messages progressifs'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])
def get_quick_loading_message(request):
    """
    Génère un message de chargement rapide.
    """
    try:
        question = request.GET.get('question', '')
        
        # Générer un message de chargement rapide
        loading_message = loading_service.get_quick_message(question)
        
        return Response({
            'success': True,
            'message': loading_message
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération du message rapide: {e}")
        return Response({
            'success': False,
            'error': 'Erreur lors de la génération du message rapide'
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
        
        # FILTRE SAR SUPPRIMÉ - Toutes les questions sont acceptées
        # Le dataset contient uniquement des questions SAR pertinentes
        
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
@permission_classes([])
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
@permission_classes([])
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
