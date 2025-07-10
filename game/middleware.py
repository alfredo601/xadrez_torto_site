# Em game/middleware.py

from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Este código é executado para cada requisição que chega
        if request.user.is_authenticated:
            now = timezone.now()
            # Define uma chave no cache (ex: 'seen_alfredddl') com a hora atual
            # O timeout de 300 segundos (5 minutos) fará a chave expirar automaticamente
            cache.set(f'seen_{request.user.username}', now, timeout=300)
            logger.debug(f"Usuário {request.user.username} marcado como online no cache")

        response = self.get_response(request)
        return response