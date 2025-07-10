import os

from django.core.asgi import get_asgi_application

# É crucial definir a variável de ambiente ANTES de fazer qualquer outro import do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xadrez_torto.settings')

# Esta linha inicializa o Django e deixa tudo pronto.
django_asgi_app = get_asgi_application()

# AGORA que o Django está pronto, podemos importar o resto com segurança.
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import game.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            game.routing.websocket_urlpatterns
        )
    ),
})