"""
Tests du consumer WebSocket du chat.

Verifie que :
- un client authentifie peut se connecter et envoyer un message ;
- le message est bien sauvegarde en base ;
- un visiteur non authentifie est refuse ;
- un client ne peut pas se connecter avec un conversation_id (reserve au staff) ;
- un membre du staff peut rejoindre la conversation d'un client precis ;
- un client non-staff ne peut pas rejoindre la conversation d'un AUTRE client
  via l'URL avec conversation_id (isolation stricte).
"""

import pytest
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.chat.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)


@pytest.mark.django_db(transaction=True)
class TestChatConsumer:
    async def test_client_authentifie_peut_se_connecter_et_envoyer_message(self):
        user = await self._create_user("client1", is_staff=False)
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        communicator.scope["user"] = user

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.send_json_to({"message": "Bonjour, j'ai une question."})
        response = await communicator.receive_json_from()

        assert response["content"] == "Bonjour, j'ai une question."
        assert response["sender_id"] == user.id
        assert response["is_staff"] is False

        await communicator.disconnect()

    async def test_message_est_sauvegarde_en_base(self):
        user = await self._create_user("client2", is_staff=False)
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        communicator.scope["user"] = user

        await communicator.connect()
        await communicator.send_json_to({"message": "Message a sauvegarder"})
        await communicator.receive_json_from()

        count = await self._count_messages_containing("Message a sauvegarder")
        assert count == 1

        await communicator.disconnect()

    async def test_visiteur_non_authentifie_est_refuse(self):
        from django.contrib.auth.models import AnonymousUser

        communicator = WebsocketCommunicator(application, "/ws/chat/")
        communicator.scope["user"] = AnonymousUser()

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_client_ne_peut_pas_utiliser_url_avec_conversation_id(self):
        user = await self._create_user("client3", is_staff=False)
        conversation = await self._create_conversation(user)
        communicator = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        communicator.scope["user"] = user

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_staff_peut_rejoindre_conversation_dun_client(self):
        client_user = await self._create_user("client4", is_staff=False)
        staff_user = await self._create_user("staff1", is_staff=True)
        conversation = await self._create_conversation(client_user)

        communicator = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        communicator.scope["user"] = staff_user

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    async def test_staff_sans_conversation_id_est_refuse(self):
        staff_user = await self._create_user("staff2", is_staff=True)
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        communicator.scope["user"] = staff_user

        connected, _ = await communicator.connect()
        assert connected is False

    @staticmethod
    async def _create_user(username, is_staff):
        from asgiref.sync import sync_to_async

        return await sync_to_async(User.objects.create_user)(
            username=username, password="MotDePasseSolide123", is_staff=is_staff
        )

    @staticmethod
    async def _create_conversation(client_user):
        from asgiref.sync import sync_to_async

        return await sync_to_async(Conversation.objects.create)(client=client_user)

    @staticmethod
    async def _count_messages_containing(text):
        from asgiref.sync import sync_to_async

        return await sync_to_async(Message.objects.filter(content__icontains=text).count)()
