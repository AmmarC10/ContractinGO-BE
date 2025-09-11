from rest_framework import generics, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from firebase_auth.models import User
from ads.models import Ad

# Generic view for GET and POST requests
class ConversationListCreateView(generics.ListCreateAPIView):
    """
    List conversations for the authenticated user or create a new conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user, is_active=True).prefetch_related('participants', 'ad', 'messages')

    def perform_create(self, serializer):
        ad_id = self.request.data.get('ad')
        other_user_id = self.request.data.get('other_user_id')

        if not ad_id or not other_user_id:
            raise serializers.ValidationError("ad and other_user_id are required")
        
        ad = get_object_or_404(Ad, id=ad_id)
        other_user = get_object_or_404(User, id=other_user_id)

        # If existing conversation, return it
        existing_conversation = Conversation.objects.filter(
            ad=ad, 
            participants=self.request.user
        ).filter(participants=other_user).first()

        if existing_conversation:
            return existing_conversation
        
        # Create new Conversation
        conversation = serializer.save(ad=ad)
        conversation.participants.add(self.request.user, other_user)
        return conversation

class ConversationDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve a specific conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user, is_active=True
        ).prefetch_related('participants', 'ad', 'messages')

class MessageListCreateView(generics.ListCreateAPIView):
    """
    List messages in a conversation or create a new message
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']

        # Verify user can access this conversation, user needs to be a participant
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        # return all messaged in conversation
        return Message.objects.filter(conversation=conversation).order_by('created_at')
    
    # POST /conversation/[conversation_id]/messages/{content}
    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']

        # Verify user can access this conversation, user needs to be a participant
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        
        serializer.save(conversation=conversation, sender=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_as_read(request, conversation_id):
    """
    Mark a message as read
    """
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )

    Message.objects.filter(conversation=conversation).exclude(sender=request.user).update(is_read=True)

    return Response({'success': True})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversation_with_user(request, user_id, ad_id):
    """
    Get or createa a conversation between current user and another user for an ad
    """
    other_user = get_object_or_404(User, id=user_id)
    ad = get_object_or_404(Ad, id=ad_id)

    conversation = Conversation.objects.filter(
        ad=ad,
        participants=request.user
    ).filter(participants=other_user).first()

    if not conversation:
        conversation = Conversation.objects.create(ad=ad)
        conversation.participants.add(request.user, other_user)
    
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """
    Get count of unread messages for the current user
    """
    unread_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    
    return Response({'unread_count': unread_count})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_conversation(request, conversation_id):
    """
    Delete a conversation
    """

    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    conversation.delete()
    return Response({'success': True})

