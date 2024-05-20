from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import ChatRoom, Message, Customer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from datetime import datetime
import random
import pusher

# Configure Pusher
pusher_client = pusher.Pusher(
  app_id='1805156',
  key='5f083f9b2bd0c3f2b6df',
  secret='da6bf312d405c9a08c0f',
  cluster='eu',
  ssl=True
)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope['url_route']['kwargs']['user_email']
        self.room = await self.get_room(self.room_name)
       
        if self.user == self.room.member1.email or self.user == self.room.member2.email:
            await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']

        timestamp = datetime.now().isoformat()
        random_integer = random.randint(1000, 10000)

        # Save the message to the database
        await self.save_message(self.room, self.user, message, timestamp, random_integer)

        # Send message to Pusher
        pusher_client.trigger(self.room_group_name, 'chat_message', {
            'id': random_integer,
            'content': message,
            'sender': sender,
            'timestamp': timestamp
        })

    @database_sync_to_async
    def get_room(self, room_id):
        room = ChatRoom.objects.get(id=room_id)
        return room

    @database_sync_to_async
    def save_message(self, room, sender, content, timestamp, random_id):
        customer = Customer.objects.get(email=sender)
        message = Message.objects.create(chat_room=room, sender=customer, content=content)
        return message
