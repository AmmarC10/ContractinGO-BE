import uuid
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Conversation, Message, MessageAttachment
from .serializers import ConversationSerializer, MessageSerializer
from supabase_auth.models import User
from ads.models import Ad
from rest_framework.parsers import MultiPartParser, FormParser
from contractingo.supabase_client import supabase

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
    parser_classes = [MultiPartParser, FormParser]

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
    def create(self, request, *args, **kwargs):
        conversation_id = request.data.get('conversation')
        content = request.data.get('content', '')
        image_file = request.FILES.get('image')
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is participant
        if request.user not in conversation.participants.all():
            return Response({
                'success': False,
                'error': 'You are not a participant in this conversation'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        # If image is provided, create message attachment
        if image_file:
            try:

                file_name = f"{request.user.id}_{uuid.uuid4()}.jpg"
                filePath = f"message-images/{file_name}"

                result = supabase.storage.from_('message-images').upload(
                    path=filePath,
                    file=image_file.read(),
                    file_options={'content-type': image_file.content_type}
                )

                image_url = supabase.storage.from_('message-images').get_public_url(filePath)

                # Create attachment
                MessageAttachment.objects.create(
                    message=message,
                    image_url=image_url,
                )

            except Exception as e:
                print(f"Error uploading image: {e}")
        
        serializer = MessageSerializer(message)

        channel_layer = get_channel_layer()
        conversation_group_name = f'conversation_{conversation_id}'
        async_to_sync(channel_layer.group_send)(
            conversation_group_name,
            {
                'type': 'conversation_message',
                'message': serializer.data,
                'sender_id': request.user.id
            }
        )

        return Response({
            'success': True,
            'data': serializer.data
        })

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
    
    return Response({
        'success': True,
        'unread_count': unread_count
        })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversation_unread_count(request, conversation_id):
    """
    Get count of unread messages for a specific conversation
    """
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )

    unread_count = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).count()
    return Response({
        'success': True,
        'unread_count': unread_count}
    )

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


