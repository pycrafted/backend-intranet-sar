from django.urls import path
from . import views
import logging

logger = logging.getLogger(__name__)

# Log au chargement du module
logger.info("=" * 80)
logger.info("🔵 [FORUM_URLS] Module urls.py chargé")
logger.info("🔵 [FORUM_URLS] Configuration des routes du forum")
logger.info("=" * 80)

app_name = 'forum'

urlpatterns = [
    # Endpoints pour les forums
    path('forums/', views.ForumListAPIView.as_view(), name='forum-list'),
    path('forums/<int:pk>/', views.ForumDetailAPIView.as_view(), name='forum-detail'),
    
    # Endpoints pour les conversations
    path('conversations/', views.ConversationListAPIView.as_view(), name='conversation-list'),
    path('conversations/<int:pk>/', views.ConversationDetailAPIView.as_view(), name='conversation-detail'),
    
    # Endpoints pour les commentaires
    path('comments/', views.CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', views.CommentDetailAPIView.as_view(), name='comment-detail'),
    
    # Endpoint pour liker/unliker un commentaire
    path('comments/<int:comment_id>/like/', views.comment_like_toggle, name='comment-like-toggle'),
]

logger.info(f"🔵 [FORUM_URLS] {len(urlpatterns)} routes configurées")
for pattern in urlpatterns:
    logger.info(f"🔵 [FORUM_URLS]   - {pattern.pattern} -> {pattern.callback}")
