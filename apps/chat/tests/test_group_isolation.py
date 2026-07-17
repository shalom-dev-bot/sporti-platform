"""
Test critique de securite : verifie qu'un message envoye dans une
conversation n'est JAMAIS recu par un client d'une AUTRE conversation,
meme si les deux sont connectees simultanement.
"""

import pytest
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from apps.accounts.models import User
from apps.chat.models import Conversation
from apps.chat.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)


@pytest.mark.django_db(transaction=True)
class TestGroupIsolation:
    async def test_message_ne_fuite_pas_vers_une_autre_conversation(self):
        from asgiref.sync import sync_to_async

        client_a = await sync_to_async(User.objects.create_user)(
            username="isol_client_a", password="MotDePasseSolide123", is_staff=False
        )
        client_b = await sync_to_async(User.objects.create_user)(
            username="isol_client_b", password="MotDePasseSolide123", is_staff=False
        )

        comm_a = WebsocketCommunicator(application, "/ws/chat/")
        comm_a.scope["user"] = client_a
        await comm_a.connect()

        comm_b = WebsocketCommunicator(application, "/ws/chat/")
        comm_b.scope["user"] = client_b
        await comm_b.connect()

        # Le client A envoie un message.
        await comm_a.send_json_to({"message": "Message prive de A"})

        # Le client A doit bien recevoir SON propre message (diffuse a son groupe).
        response_a = await comm_a.receive_json_from()
        assert response_a["content"] == "Message prive de A"

        # Le client B ne doit RIEN recevoir : aucun message ne doit fuiter
        # vers son groupe, qui est totalement different.
        assert await comm_b.receive_nothing(timeout=1) is True

        await comm_a.disconnect()
        await comm_b.disconnect()

    async def test_deux_conversations_ont_bien_des_groupes_differents(self):
        from asgiref.sync import sync_to_async

        client_a = await sync_to_async(User.objects.create_user)(
            username="isol_client_c", password="MotDePasseSolide123", is_staff=False
        )
        client_b = await sync_to_async(User.objects.create_user)(
            username="isol_client_d", password="MotDePasseSolide123", is_staff=False
        )

        conv_a = await sync_to_async(Conversation.objects.get_or_create)(client=client_a)
        conv_b = await sync_to_async(Conversation.objects.get_or_create)(client=client_b)

        assert conv_a[0].id != conv_b[0].id
