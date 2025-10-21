"""
Vues hybrides pour l'intégration du système vectoriel avec le chatbot MAÏ.
Combine la recherche vectorielle et heuristique avec fallback intelligent.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
import json

from mai.vector_search_service import vector_search_service
from mai.embedding_service import embedding_service
from mai.services import MAIService
from mai.models import RAGSearchLog

logger = logging.getLogger(__name__)

class HybridSearchView(View):
    """
    Vue hybride qui combine recherche vectorielle et heuristique.
    Utilise la recherche vectorielle en priorité avec fallback vers l'heuristique.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Recherche hybride avec fallback intelligent"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            limit = min(int(data.get('limit', 5)), 10)
            threshold = float(data.get('threshold', 0.4))
            use_fallback = data.get('use_fallback', True)
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': 'Query requise'
                }, status=400)
            
            start_time = time.time()
            
            # Étape 1: Essayer la recherche vectorielle
            vector_results = self._try_vector_search(query, limit, threshold)
            
            if vector_results and len(vector_results) > 0:
                # Succès avec recherche vectorielle
                search_time = time.time() - start_time
                
                # Logger la recherche
                RAGSearchLog.log_search(
                    query=query,
                    method='vectorial',
                    results_count=len(vector_results),
                    response_time_ms=int(search_time * 1000),
                    success=True
                )
                
                return JsonResponse({
                    'success': True,
                    'results': vector_results,
                    'method': 'vectorial',
                    'total': len(vector_results),
                    'response_time_ms': int(search_time * 1000)
                })
            
            # Étape 2: Fallback vers recherche heuristique si activé
            if use_fallback:
                heuristic_results = self._try_heuristic_search(query, limit)
                search_time = time.time() - start_time
                
                if heuristic_results and len(heuristic_results) > 0:
                    # Succès avec recherche heuristique
                    RAGSearchLog.log_search(
                        query=query,
                        method='heuristic',
                        results_count=len(heuristic_results),
                        response_time_ms=int(search_time * 1000),
                        success=True
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'results': heuristic_results,
                        'method': 'heuristic',
                        'total': len(heuristic_results),
                        'response_time_ms': int(search_time * 1000)
                    })
            
            # Échec des deux méthodes
            search_time = time.time() - start_time
            RAGSearchLog.log_search(
                query=query,
                method='hybrid',
                results_count=0,
                response_time_ms=int(search_time * 1000),
                success=False,
                error_message='Aucun résultat trouvé'
            )
            
            return JsonResponse({
                'success': False,
                'results': [],
                'method': 'none',
                'total': 0,
                'error': 'Aucun résultat trouvé'
            })
            
        except Exception as e:
            logger.error(f"Erreur recherche hybride: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)
    
    def _try_vector_search(self, query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Tente une recherche vectorielle"""
        try:
            results = vector_search_service.search_similar(query, limit, threshold)
            
            formatted_results = []
            for doc in results:
                try:
                    metadata = json.loads(doc.metadata) if isinstance(doc.metadata, str) else doc.metadata
                    formatted_results.append({
                        'content': doc.content_text,
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'similarity': getattr(doc, 'similarity', 0.0),
                        'source': metadata.get('source', 'unknown'),
                        'metadata': metadata
                    })
                except Exception as e:
                    logger.warning(f"Erreur formatage résultat vectoriel: {e}")
                    continue
            
            return formatted_results
            
        except Exception as e:
            logger.warning(f"Erreur recherche vectorielle: {e}")
            return []
    
    def _try_heuristic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Tente une recherche heuristique (fallback)"""
        try:
            mai_service = MAIService()
            
            # Utiliser l'ancien système heuristique
            context = mai_service.get_context_for_question(query)
            
            if context and context.strip():
                # Parser le contexte heuristique pour extraire Q/R
                formatted_results = self._parse_heuristic_context(context, query)
                return formatted_results[:limit]
            
            return []
            
        except Exception as e:
            logger.warning(f"Erreur recherche heuristique: {e}")
            return []
    
    def _parse_heuristic_context(self, context: str, query: str) -> List[Dict[str, Any]]:
        """Parse le contexte heuristique pour extraire les Q/R"""
        try:
            # Le contexte heuristique a un format spécifique
            # On essaie d'extraire les questions et réponses
            lines = context.split('\n')
            results = []
            
            current_question = ""
            current_answer = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    # Nouvelle question
                    if current_question and current_answer:
                        results.append({
                            'content': f"Q: {current_question}\nA: {current_answer}",
                            'question': current_question,
                            'answer': current_answer,
                            'similarity': 0.5,  # Similarité par défaut pour heuristique
                            'source': 'heuristic_fallback',
                            'metadata': {
                                'question': current_question,
                                'answer': current_answer,
                                'source': 'heuristic_fallback',
                                'method': 'heuristic'
                            }
                        })
                    
                    current_question = line[2:].strip()  # Enlever le numéro
                    current_answer = ""
                elif line.startswith('Réponse:') or line.startswith('   Réponse:'):
                    current_answer = line.replace('Réponse:', '').strip()
                elif current_question and not current_answer:
                    # Ligne de réponse sans préfixe
                    current_answer = line
            
            # Ajouter la dernière Q/R
            if current_question and current_answer:
                results.append({
                    'content': f"Q: {current_question}\nA: {current_answer}",
                    'question': current_question,
                    'answer': current_answer,
                    'similarity': 0.5,
                    'source': 'heuristic_fallback',
                    'metadata': {
                        'question': current_question,
                        'answer': current_answer,
                        'source': 'heuristic_fallback',
                        'method': 'heuristic'
                    }
                })
            
            return results
            
        except Exception as e:
            logger.warning(f"Erreur parsing contexte heuristique: {e}")
            return []


class HybridContextView(View):
    """
    Vue pour récupérer le contexte hybride optimisé pour le chatbot.
    Compatible avec l'API existante du frontend.
    """
    
    def get(self, request):
        """Récupère le contexte hybride pour une question"""
        try:
            query = request.GET.get('question', '').strip()
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'context': '',
                    'error': 'Question requise'
                }, status=400)
            
            start_time = time.time()
            
            # Utiliser la recherche hybride
            hybrid_view = HybridSearchView()
            response_data = hybrid_view._try_vector_search(query, 3, 0.4)
            
            if not response_data:
                # Fallback vers heuristique
                response_data = hybrid_view._try_heuristic_search(query, 3)
            
            search_time = time.time() - start_time
            
            if response_data and len(response_data) > 0:
                # Construire le contexte au format attendu par le frontend
                context = "Contexte SAR trouvé:\n\n"
                for i, result in enumerate(response_data, 1):
                    context += f"{i}. {result['question']}\n"
                    context += f"   Réponse: {result['answer']}\n\n"
                
                return JsonResponse({
                    'success': True,
                    'context': context,
                    'query': query,
                    'method': 'hybrid',
                    'response_time_ms': int(search_time * 1000)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'context': '',
                    'query': query,
                    'error': 'Aucun contexte trouvé'
                })
                
        except Exception as e:
            logger.error(f"Erreur contexte hybride: {e}")
            return JsonResponse({
                'success': False,
                'context': '',
                'error': 'Erreur interne du serveur'
            }, status=500)


class ABTestingView(View):
    """
    Vue pour les tests A/B entre système vectoriel et heuristique.
    Permet de comparer les performances des deux systèmes.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Test A/B entre vectoriel et heuristique"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            test_mode = data.get('test_mode', 'both')  # 'vectorial', 'heuristic', 'both'
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': 'Query requise'
                }, status=400)
            
            results = {}
            
            # Test vectoriel
            if test_mode in ['vectorial', 'both']:
                vector_start = time.time()
                vector_results = vector_search_service.search_similar(query, 5, 0.4)
                vector_time = time.time() - vector_start
                
                results['vectorial'] = {
                    'success': len(vector_results) > 0,
                    'results_count': len(vector_results),
                    'response_time_ms': int(vector_time * 1000),
                    'results': [
                        {
                            'question': json.loads(doc.metadata).get('question', '') if isinstance(doc.metadata, str) else doc.metadata.get('question', ''),
                            'answer': json.loads(doc.metadata).get('answer', '') if isinstance(doc.metadata, str) else doc.metadata.get('answer', ''),
                            'similarity': getattr(doc, 'similarity', 0.0)
                        }
                        for doc in vector_results
                    ]
                }
            
            # Test heuristique
            if test_mode in ['heuristic', 'both']:
                heuristic_start = time.time()
                mai_service = MAIService()
                heuristic_context = mai_service.get_context_for_question(query)
                heuristic_time = time.time() - heuristic_start
                
                results['heuristic'] = {
                    'success': bool(heuristic_context and heuristic_context.strip()),
                    'context_length': len(heuristic_context) if heuristic_context else 0,
                    'response_time_ms': int(heuristic_time * 1000),
                    'context': heuristic_context
                }
            
            return JsonResponse({
                'success': True,
                'query': query,
                'test_mode': test_mode,
                'results': results,
                'comparison': self._compare_results(results)
            })
            
        except Exception as e:
            logger.error(f"Erreur test A/B: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)
    
    def _compare_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare les résultats des deux systèmes"""
        comparison = {}
        
        if 'vectorial' in results and 'heuristic' in results:
            vectorial = results['vectorial']
            heuristic = results['heuristic']
            
            comparison = {
                'vectorial_faster': vectorial['response_time_ms'] < heuristic['response_time_ms'],
                'vectorial_more_results': vectorial['results_count'] > 0,
                'heuristic_has_context': heuristic['success'],
                'performance_ratio': heuristic['response_time_ms'] / vectorial['response_time_ms'] if vectorial['response_time_ms'] > 0 else 0,
                'recommendation': self._get_recommendation(vectorial, heuristic)
            }
        
        return comparison
    
    def _get_recommendation(self, vectorial: Dict[str, Any], heuristic: Dict[str, Any]) -> str:
        """Génère une recommandation basée sur les résultats"""
        if vectorial['success'] and vectorial['response_time_ms'] < heuristic['response_time_ms']:
            return 'vectorial'
        elif heuristic['success'] and not vectorial['success']:
            return 'heuristic'
        elif vectorial['success'] and heuristic['success']:
            return 'hybrid'
        else:
            return 'none'


class MonitoringView(View):
    """
    Vue de monitoring pour surveiller les performances du système hybride.
    """
    
    def get(self, request):
        """Récupère les métriques de monitoring"""
        try:
            hours = int(request.GET.get('hours', 24))
            
            # Statistiques des recherches
            stats = vector_search_service.get_search_stats(hours)
            
            # Statistiques des logs
            from django.utils import timezone
            from datetime import timedelta
            from django.db import models
            
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            logs = RAGSearchLog.objects.filter(created_at__range=(start_time, end_time))
            
            method_stats = {}
            for method in ['vectorial', 'heuristic', 'hybrid']:
                method_logs = logs.filter(method=method)
                method_stats[method] = {
                    'total_searches': method_logs.count(),
                    'successful_searches': method_logs.filter(success=True).count(),
                    'avg_response_time': method_logs.aggregate(
                        avg_time=models.Avg('response_time_ms')
                    )['avg_time'] or 0,
                    'avg_results': method_logs.aggregate(
                        avg_results=models.Avg('results_count')
                    )['avg_results'] or 0
                }
            
            # Statistiques de performance
            performance_stats = {
                'total_searches': logs.count(),
                'success_rate': (logs.filter(success=True).count() / logs.count() * 100) if logs.count() > 0 else 0,
                'avg_response_time': logs.aggregate(
                    avg_time=models.Avg('response_time_ms')
                )['avg_time'] or 0,
                'method_breakdown': method_stats
            }
            
            return JsonResponse({
                'success': True,
                'period_hours': hours,
                'performance': performance_stats,
                'vector_stats': stats,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur monitoring: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=500)
