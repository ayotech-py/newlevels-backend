"""
ASGI config for newlevels project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from newlevelsapi.routing import websocket_urlpatterns
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newlevels.settings')

#application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
                    URLRouter(
                        websocket_urlpatterns
                    )
            ),
})


