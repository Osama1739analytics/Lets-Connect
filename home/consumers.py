import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import DirectMessage

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We expect user_id in the URL route: ws/chat/<int:user_id>/
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope['user']
        
        # Check authentication
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Create a deterministic room name
        # Sorting ensures both users connect to the exact same room string
        ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_group_name = f'chat_{ids[0]}_{ids[1]}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action', 'send')
        
        if action == 'edit':
            message_id = text_data_json['message_id']
            new_content = text_data_json['message']
            # Broadcast edit
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_edit',
                    'id': message_id,
                    'message': new_content
                }
            )
        else:
            message_content = text_data_json['message']
            # Save to database
            new_msg = await self.save_message(self.user.id, self.other_user_id, message_content)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'id': new_msg.id,
                    'message': new_msg.content,
                    'sender_id': self.user.id,
                    'timestamp': new_msg.timestamp.strftime('%I:%M %p')
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'id': event['id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
        }))

    async def message_edit(self, event):
        # Send edit event to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'edit',
            'id': event['id'],
            'message': event['message']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, content):
        msg = DirectMessage.objects.create(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content
        )
        # Create notification for recipient
        from .models import Notification
        from django.urls import reverse
        Notification.objects.create(
            recipient_id=recipient_id,
            sender_id=sender_id,
            verb=f"sent you a message: {content[:30]}...",
            link=reverse('home:chat_room', args=[sender_id])
        )
        return msg

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
            
        self.room_group_name = f'notify_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'verb': event['verb'],
            'sender': event['sender'],
            'sender_id': event.get('sender_id'),
            'timestamp': 'Just now',
            'link': event.get('link', '#')
        }))
