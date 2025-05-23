"""
ASGI config for odintrack_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# DO NOT import tracker.routing here yet

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'odintrack_project.settings')
django.setup() # Call django.setup() explicitly here

# NOW import tracker.routing, AFTER django.setup()
import tracker.routing

# Get the default HTTP ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AuthMiddlewareStack( # Use AuthMiddlewareStack to access user in consumer
        URLRouter(
            tracker.routing.websocket_urlpatterns
        )
    ),
})
