from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from .guacdproxy import GuacamoleConsumer

# Channels 3: the plain HTTP protocol is no longer added implicitly, and
# consumers must be wired in as ASGI apps via .as_asgi().
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('tunnelws/ticket/<uuid:ticket>/', GuacamoleConsumer.as_asgi()),
        ])
    ),
})
