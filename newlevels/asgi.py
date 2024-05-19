"""
ASGI config for newlevels project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from newlevelsapi.routing import websocket_urlpatterns

application = get_asgi_application()


