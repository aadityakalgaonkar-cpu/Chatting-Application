import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RealTimeChat.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import services.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(
        URLRouter(
            services.routing.websocket_urlpatterns
        )
    ),
})