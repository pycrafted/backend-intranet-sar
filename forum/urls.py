from django.urls import path
from . import views

urlpatterns = [
    # Forums
    path('', views.ForumListAPIView.as_view(), name='forum-list'),
    path('create/', views.ForumCreateAPIView.as_view(), name='forum-create'),
    path('<int:pk>/', views.ForumDetailAPIView.as_view(), name='forum-detail'),
    path('<int:pk>/update/', views.ForumUpdateAPIView.as_view(), name='forum-update'),
    path('<int:pk>/delete/', views.ForumDeleteAPIView.as_view(), name='forum-delete'),
    
    # Messages
    path('<int:forum_id>/messages/', views.ForumMessageListAPIView.as_view(), name='forum-messages'),
    path('<int:forum_id>/messages/create/', views.ForumMessageCreateAPIView.as_view(), name='forum-message-create'),
    path('messages/<int:pk>/update/', views.ForumMessageUpdateAPIView.as_view(), name='forum-message-update'),
    path('messages/<int:pk>/delete/', views.ForumMessageDeleteAPIView.as_view(), name='forum-message-delete'),
]
