from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import ChatRoom, Message, Customer
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from datetime import datetime
import random


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #print(self.scope)
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_name}'

        # Authorization: Check if the user is part of this room
        #self.user = 'ayotech@gmail.com'
        self.user = self.scope['url_route']['kwargs']['user_email']
        self.room = await self.get_room(self.room_name)
       
        if self.user == self.room.member1.email or self.user == self.room.member2.email:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']

        print(message)
        print(sender)

        timestamp = datetime.now().isoformat()
        random_integer = random.randint(1000, 10000)

        # Save the message to the database
        await self.save_message_and_send_to_group(self.room, self.user, message, timestamp, random_integer)

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        timestamp = event['timestamp']
        random_id = event['id']
        sender = event['sender']
        print("message sending")

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'id': random_id,
            'content': message,
            'sender': sender,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_room(self, room_id):
        room = ChatRoom.objects.get(id=room_id)
        print(room)
        return room

    @database_sync_to_async
    def get_customer(self, email):
        customer_email = Customer.objects.get(email=email).email
        return customer_email

    @database_sync_to_async
    def save_message_and_send_to_group(self, room, sender, content, timestamp, random_id):
        customer = Customer.objects.get(email=sender)
        message = Message.objects.create(chat_room=room, sender=customer, content=content)
        
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'id': random_id,
                'type': 'chat_message',
                'message': content,
                'timestamp': timestamp,
                'sender': customer.email
            }
        )
