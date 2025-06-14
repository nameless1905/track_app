# your_project/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import myapp.routing  # Импорт маршрутов приложения

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        myapp.routing.websocket_urlpatterns
    ),
})