# Em game/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/presence/$', consumers.PresenceConsumer.as_asgi()),
    re_path(r'ws/pvp/game/(?P<game_id>\d+)/$', consumers.PvPGameConsumer.as_asgi()),
]