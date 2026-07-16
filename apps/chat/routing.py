"""Routes WebSocket du chat. Chaque conversation est isolee dans son propre
groupe Channels (conversation_<id>) : un message n'est jamais diffuse a
plus de personnes que necessaire."""

from django.urls import re_path

from .consumers.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/$", ChatConsumer.as_asgi()),
]
