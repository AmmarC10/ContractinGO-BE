from django.urls import path
from . import views

urlpatterns = [
    # Conversation endpoints
    path('conversations/', views.ConversationListCreateView.as_view(), name='conversation-list-create'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    
    # Utility endpoints
    path('conversations/<int:conversation_id>/mark-read/', views.mark_as_read, name='mark-messages-read'),
    path('conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete-conversation'),
    path('conversations/<int:conversation_id>/unread-count/', views.get_conversation_unread_count, name='conversation-unread-count'),
    path('conversations/with-user/<int:user_id>/ad/<int:ad_id>/', views.get_conversation_with_user, name='get-conversation-with-user'),
    path('conversations/unread-count/', views.get_unread_count, name='unread-count'),
    
]