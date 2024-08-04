import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from reader.consumers import EmailConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mail_reader.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/mail-server/', EmailConsumer.as_asgi()),
        ])
    ),
})