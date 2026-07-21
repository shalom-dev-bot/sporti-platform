"""
Audit centralise du cloisonnement des conversations : rassemble et
verifie TOUS les points d'entree possibles vers les donnees d'une
conversation, pour prouver de maniere synthetique qu'un client ne peut
jamais acceder aux echanges d'un autre client.

C'est la garantie de confidentialite centrale du projet SPORTI.
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from apps.accounts.models import User
from apps.chat.models import Attachment, Conversation, Message
from apps.chat.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)


class ConversationIsolationHTTPTests(TestCase):
    """Verifie l'isolation sur tous les endpoints HTTP/API."""

    def setUp(self):
        self.client_a = User.objects.create_user(
            username="audit_iso_a", password="MotDePasseSolide123", is_staff=False
        )
        self.client_b = User.objects.create_user(
            username="audit_iso_b", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation_a = Conversation.objects.create(client=self.client_a)
        Message.objects.create(
            conversation=self.conversation_a, sender=self.client_a, content="Message prive de A"
        )

    def test_point_1_historique_conversation_inaccessible_a_un_autre_client(self):
        self.client.login(username="audit_iso_b", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation_a.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_point_2_upload_impossible_dans_conversation_dun_autre_client(self):
        self.client.login(username="audit_iso_b", password="MotDePasseSolide123")
        fichier = SimpleUploadedFile("test.mp3", b"contenu", content_type="audio/mpeg")
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation_a.id]),
            {"file": fichier},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Attachment.objects.filter(message__conversation=self.conversation_a).count(), 0
        )

    def test_point_3_liste_conversations_reservee_au_staff_pas_aux_clients(self):
        self.client.login(username="audit_iso_b", password="MotDePasseSolide123")
        response = self.client.get(reverse("chat:api_conversations"))
        self.assertEqual(response.status_code, 403)

    def test_point_4_dashboard_admin_inaccessible_a_un_client(self):
        self.client.login(username="audit_iso_b", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("dashboard:conversation_detail", args=[self.conversation_a.id])
        )
        self.assertEqual(response.status_code, 302)  # redirection vers connexion

    def test_point_5_visiteur_non_authentifie_ne_voit_rien(self):
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation_a.id])
        )
        self.assertEqual(response.status_code, 403)


@pytest.mark.django_db(transaction=True)
class TestConversationIsolationWebSocket:
    """Verifie l'isolation sur le canal temps reel (WebSocket)."""

    async def test_point_6_client_ne_peut_pas_rejoindre_conversation_par_id(self):
        client_a = await sync_to_async(User.objects.create_user)(
            username="audit_iso_ws_a", password="MotDePasseSolide123", is_staff=False
        )
        conversation = await sync_to_async(Conversation.objects.create)(client=client_a)

        client_b = await sync_to_async(User.objects.create_user)(
            username="audit_iso_ws_b", password="MotDePasseSolide123", is_staff=False
        )

        # Client B tente de rejoindre la conversation de A via son ID direct.
        comm = WebsocketCommunicator(application, f"/ws/chat/{conversation.id}/")
        comm.scope["user"] = client_b

        connected, _ = await comm.connect()
        # Refuse : seul le staff peut rejoindre une conversation par ID.
        assert connected is False

    async def test_point_7_message_ne_fuite_jamais_vers_un_autre_client_connecte(self):
        client_a = await sync_to_async(User.objects.create_user)(
            username="audit_iso_ws_c", password="MotDePasseSolide123", is_staff=False
        )
        client_b = await sync_to_async(User.objects.create_user)(
            username="audit_iso_ws_d", password="MotDePasseSolide123", is_staff=False
        )

        comm_a = WebsocketCommunicator(application, "/ws/chat/")
        comm_a.scope["user"] = client_a
        await comm_a.connect()

        comm_b = WebsocketCommunicator(application, "/ws/chat/")
        comm_b.scope["user"] = client_b
        await comm_b.connect()

        await comm_a.send_json_to({"message": "Confidentiel pour A uniquement"})
        await comm_a.receive_json_from()

        # B ne doit RIEN recevoir de la conversation de A.
        assert await comm_b.receive_nothing(timeout=1) is True

        await comm_a.disconnect()
        await comm_b.disconnect()
