"""
Tests des statuts de message (comme WhatsApp) et de l'indicateur de frappe.
"""

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.chat.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)


async def _receive_until(comm, expected_type, max_tries=5):
    """Lit les messages recus jusqu'a trouver celui du type attendu,
    en ignorant les evenements annexes (ex: presence) qui peuvent
    arriver avant, exactement comme un vrai client les ignorerait."""
    for _ in range(max_tries):
        response = await comm.receive_json_from()
        if response.get("type", "message") == expected_type or (
            expected_type == "message" and "content" in response
        ):
            return response
    raise AssertionError(f"Type '{expected_type}' jamais recu apres {max_tries} essais.")


@pytest.mark.django_db(transaction=True)
class TestReadStatusAndTyping:
    async def test_message_reste_sent_si_destinataire_non_connecte(self):
        client_user = await sync_to_async(User.objects.create_user)(
            username="rs_client1", password="MotDePasseSolide123", is_staff=False
        )
        comm = WebsocketCommunicator(application, "/ws/chat/")
        comm.scope["user"] = client_user
        try:
            await comm.connect()
            await comm.send_json_to({"message": "Personne pour me lire"})
            response = await _receive_until(comm, "message")
            assert response["status"] == "sent"
        finally:
            await comm.disconnect()

    async def test_message_passe_a_delivered_si_destinataire_connecte(self):
        client_user = await sync_to_async(User.objects.create_user)(
            username="rs_client2", password="MotDePasseSolide123", is_staff=False
        )
        staff_user = await sync_to_async(User.objects.create_user)(
            username="rs_staff1", password="MotDePasseSolide123", is_staff=True
        )
        conversation = await sync_to_async(Conversation.objects.create)(client=client_user)

        comm_client = WebsocketCommunicator(application, "/ws/chat/")
        comm_client.scope["user"] = client_user
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        comm_staff.scope["user"] = staff_user
        try:
            await comm_client.connect()
            await comm_staff.connect()

            await comm_client.send_json_to({"message": "Le staff est present"})
            response = await _receive_until(comm_client, "message")
            assert response["status"] == "delivered"
        finally:
            await comm_client.disconnect()
            await comm_staff.disconnect()

    async def test_message_passe_a_read_quand_destinataire_ouvre_conversation(self):
        client_user = await sync_to_async(User.objects.create_user)(
            username="rs_client3", password="MotDePasseSolide123", is_staff=False
        )
        staff_user = await sync_to_async(User.objects.create_user)(
            username="rs_staff2", password="MotDePasseSolide123", is_staff=True
        )
        conversation = await sync_to_async(Conversation.objects.create)(client=client_user)

        comm_client = WebsocketCommunicator(application, "/ws/chat/")
        comm_client.scope["user"] = client_user
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        comm_staff.scope["user"] = staff_user
        try:
            await comm_client.connect()
            await comm_client.send_json_to({"message": "En attente de lecture"})
            await _receive_until(comm_client, "message")

            await comm_staff.connect()

            receipt = await _receive_until(comm_client, "read_receipt")
            assert receipt["status"] == "read"

            get_message = sync_to_async(
                lambda: Message.objects.get(
                    conversation=conversation, content="En attente de lecture"
                )
            )
            message = await get_message()
            assert message.status == Message.Status.READ
        finally:
            await comm_client.disconnect()
            await comm_staff.disconnect()

    async def test_indicateur_de_frappe_est_diffuse_a_lautre_partie(self):
        client_user = await sync_to_async(User.objects.create_user)(
            username="typ_client1", password="MotDePasseSolide123", is_staff=False
        )
        staff_user = await sync_to_async(User.objects.create_user)(
            username="typ_staff1", password="MotDePasseSolide123", is_staff=True
        )
        conversation = await sync_to_async(Conversation.objects.create)(client=client_user)

        comm_client = WebsocketCommunicator(application, "/ws/chat/")
        comm_client.scope["user"] = client_user
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        comm_staff.scope["user"] = staff_user
        try:
            await comm_client.connect()
            await comm_staff.connect()

            await comm_client.send_json_to({"type": "typing", "is_typing": True})

            response = await _receive_until(comm_staff, "typing")
            assert response["is_typing"] is True
            assert response["user_id"] == client_user.id
        finally:
            await comm_client.disconnect()
            await comm_staff.disconnect()

    async def test_la_personne_qui_tape_ne_recoit_pas_son_propre_indicateur(self):
        client_user = await sync_to_async(User.objects.create_user)(
            username="typ_client2", password="MotDePasseSolide123", is_staff=False
        )
        comm = WebsocketCommunicator(application, "/ws/chat/")
        comm.scope["user"] = client_user
        try:
            await comm.connect()
            await comm.send_json_to({"type": "typing", "is_typing": True})
            assert await comm.receive_nothing(timeout=1) is True
        finally:
            await comm.disconnect()
