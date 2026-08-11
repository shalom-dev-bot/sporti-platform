"""Routes WebSocket du chat. Chaque conversation est isolee dans son propre
groupe Channels (conversation_<id>) : un message n'est jamais diffuse a
plus de personnes que necessaire.

- ws/chat/                    -> connexion cote client (sa propre conversation)
- ws/chat/<conversation_id>/  -> connexion cote entreprise (staff uniquement)
"""

from django.urls import re_path

from .consumers.admin_dashboard_consumer import AdminDashboardConsumer
from .consumers.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/chat/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/admin/dashboard/$", AdminDashboardConsumer.as_asgi()),
]
