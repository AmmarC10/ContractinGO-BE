import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message, MessageAttachment
from .serializers import MessageSerializer
from jose import jwt, JWTError
from supabase_auth.models import User


"""
WEBSOCKETS:
    
    Traditional HTTP: 
        - Client asks for data/message -> Server sends data/message -> Connection closes
        - Problem with traditional HTTP is that the user has to keep asking (polling), slow and inefficient

    Websockets: 
        - Client says lets keep talking -> Server says sure -> Connection stays opne
        - Data is sent in real-time and in both directions (bidirectional)
        - Connection stays open until either client or server closes it, perfect for chat and notifications

    Django Channels Architecture:
        - Django itself is synchronous and can't hanlde websockets, Django Channels extends Django to support websockets
        - Frontend Websocket URL: ws://.../conversation/123/?token=xyz -> ASGI Server (Daphne)
        -> Channel Layer( Manages groups/broadcasting to multiple users) -> ConversationConsumer (consumers.py) handles websocket events
    
"""

# Websocket handler that manages a single conversatoin room
class ConversationConsumer(AsyncWebsocketConsumer):

    # When a user first connects to the websocket
    async def connect(self):
        # URL: ws://.../conversation/{conversation_id}
        # self.scope contains url, headers, query params, similar to django request object but for websockets
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'conversation_{self.conversation_id}'

        # Get supabase token from query params
        # URL: ws://...?token=xyz
        query_string = self.scope['query_string'].decode() if self.scope['query_string'] else ''
        query_params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
        
        token = query_params.get('token')

        if not token:
            await self.close(code=4004, reason='Token is required')
            return
        
        # Authenticate user with supabase
        # Websockets can't set HTTP headers so pass auth token as query param
        user = await self.authenticate_supabase_user(token)
        if not user:
            await self.close(code=4004, reason='Invalid token')
            return
        
        # Ensure user is part of the conversation
        # In normal Django views, middleware checks auth automatically, but websockets need to do it manually
        if not await self.check_user_permission(user, self.conversation_id):
            await self.close(code=4004, reason='You are not allowed to access this conversation')
            return
        
        self.scope['user'] = user
        await self.channel_layer.group_add(self.conversation_group_name, self.channel_name)

        await self.accept()
    
    # Runs when user closes browser tab, network drops, user navigates away, connection times out
    async def disconnect(self, close_code):
        # Leave conversation group
        await self.channel_layer.group_discard(self.conversation_group_name, self.channel_name)
    
    # Runs when client sneds data to server
    async def receive(self, text_data):
        try:
            # parse JSON
            data = json.loads(text_data)
            message_type = data.get('type')

            # Handle different message types
            if message_type == 'send_message':
                await self.send_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error processing message: {str(e)}'}))

    

    async def send_message(self, data):
        user = self.scope['user'] # get authenticated user
        content = data.get('content') # get message content
        image_url = data.get('image_url') # get optional image url

        # Validate
        if not content and not image_url:
            await self.send(text_data=json.dumps({
                'error': 'Message content or image required'
            }))
            return
        
        # Create message in db
        message = await self.create_message(user, content, image_url)

        # Serialize message
        message_data = await self.serialize_message(message)

        # Broadcast message to all users in conversation group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'conversation_message', # calls conversation_message() method
                'message': message_data,
                'sender_id': user.id
            }
        )
    
    async def handle_typing(self, data):
        user = self.scope['user']
        is_typing = data.get('is_typing', False)

        # Send typing notification to conversation group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing_status',
                'user_id': user.id,
                'user_name': user.name,
                'is_typing': is_typing
            }
        )
    
    # Group_sned (broadcasts to all) -> conversation_message runs on each connection -> self.send sends to specific users browser
    async def conversation_message(self, event):
        # Send message to websocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_status(self, event):
        # Send typing status to websocket (exclude sender)
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))

    # @database_sync_to_async decorator lets async code use Django ORM (which is sync), otherwise async code would freeze waiting for db
    @database_sync_to_async
    def authenticate_supabase_user(self, token):
        try:
            jwt_secret = os.getenv('SUPABASE_JWT_SECRET')

            if not jwt_secret:
                print("SUPABASE_JWT_SECRET not found in environment")
                return None
            
            payload = jwt.decode(token , jwt_secret, algorithms=['HS256'], audience='authenticated')

            uid = payload.get('sub')
            if not uid:
                print("No 'sub' claim in token")
                return None
            
            # Get user
            user = User.objects.get(uid=uid)
            return user

        except JWTError as e:
            print(f"Supabase JWT verification error: {e}")
            return None
        except User.DoesNotExist:
            print(f"User with uid {uid} not found in database")
            return None
        except Exception as e:
            print(f"Supabase authentication error: {e}")
            return None
        
    @database_sync_to_async
    def check_user_permission(self, user, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_message(self, user, content, image_url=None):
        # Create new message in database
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )

        if image_url:
            MessageAttachment.objects.create(
                message=message,
                image_url=image_url
            )

        return message
    
    @database_sync_to_async
    def serialize_message(self, message):
        serializer = MessageSerializer(message)
        return serializer.data

