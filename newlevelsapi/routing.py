# chat/routing.py
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_id>\w+)/(?P<user_email>[^/]+)', ChatConsumer.as_asgi()),
]