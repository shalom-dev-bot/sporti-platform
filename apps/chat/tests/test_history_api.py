"""
Tests de l'API d'historique des conversations.

Verifie que :
- le staff peut lister toutes les conversations ;
- un client ne peut PAS lister toutes les conversations ;
- un client peut consulter SA PROPRE conversation ;
- un client ne peut PAS consulter la conversation d'un AUTRE client ;
- le staff peut consulter n'importe quelle conversation ;
- l'historique est bien pagine.
"""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.chat.models import Conversation, Message


class ConversationHistoryAPITests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_test", password="MotDePasseSolide123", is_staff=True
        )
        self.client1 = User.objects.create_user(
            username="client_a", password="MotDePasseSolide123", is_staff=False
        )
        self.client2 = User.objects.create_user(
            username="client_b", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation1 = Conversation.objects.create(client=self.client1)
        for i in range(5):
            Message.objects.create(
                conversation=self.conversation1, sender=self.client1, content=f"Message {i}"
            )

    def test_staff_peut_lister_les_conversations(self):
        self.client.login(username="staff_test", password="MotDePasseSolide123")
        response = self.client.get(reverse("chat:api_conversations"))
        self.assertEqual(response.status_code, 200)

    def test_client_ne_peut_pas_lister_les_conversations(self):
        self.client.login(username="client_a", password="MotDePasseSolide123")
        response = self.client.get(reverse("chat:api_conversations"))
        self.assertEqual(response.status_code, 403)

    def test_client_peut_consulter_sa_propre_conversation(self):
        self.client.login(username="client_a", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation1.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 5)

    def test_client_ne_peut_pas_consulter_conversation_dun_autre(self):
        self.client.login(username="client_b", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation1.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_peut_consulter_nimporte_quelle_conversation(self):
        self.client.login(username="staff_test", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation1.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_conversation_introuvable_renvoie_404(self):
        self.client.login(username="staff_test", password="MotDePasseSolide123")
        response = self.client.get(reverse("chat:api_conversation_history", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_visiteur_non_connecte_est_refuse(self):
        response = self.client.get(reverse("chat:api_conversations"))
        self.assertEqual(response.status_code, 403)
