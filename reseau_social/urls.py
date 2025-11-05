from django.urls import path
from . import views

urlpatterns = [
    # Conversations
    path('conversations/', views.ConversationListCreateView.as_view(), name='conversation-list-create'),
    path('conversations/create-with-user/', views.create_conversation_with_user, name='create-conversation-with-user'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    
    # Messages
    path('conversations/<int:conversation_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    
    # Marquer les messages comme lus
    path('conversations/<int:conversation_id>/mark-read/', views.MarkMessagesReadView.as_view(), name='mark-messages-read'),
    
    # Participants
    path('conversations/<int:conversation_id>/participants/', views.ConversationParticipantsView.as_view(), name='conversation-participants'),
    
    # Recherche d'utilisateurs
    path('users/search/', views.user_search, name='user-search'),
]

