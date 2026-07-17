"""
Verification de la pagination par curseur avec un volume realiste de
messages, pour confirmer que le scroll infini aura bien des donnees
coherentes a consommer cote frontend.
"""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.chat.models import Conversation, Message


class PaginationStressTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_pagination", password="MotDePasseSolide123", is_staff=True
        )
        self.client_user = User.objects.create_user(
            username="client_pagination", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.client_user)

        # 50 messages : page_size=30, donc on attend 2 pages (30 + 20).
        for i in range(50):
            Message.objects.create(
                conversation=self.conversation,
                sender=self.client_user,
                content=f"Message numero {i}",
            )

    def test_premiere_page_contient_30_messages(self):
        self.client.login(username="staff_pagination", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation.id])
        )
        data = response.json()
        self.assertEqual(len(data["results"]), 30)
        self.assertIsNotNone(data["next"])

    def test_deuxieme_page_contient_les_20_messages_restants(self):
        self.client.login(username="staff_pagination", password="MotDePasseSolide123")
        first_response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation.id])
        )
        next_url = first_response.json()["next"]

        second_response = self.client.get(next_url)
        data = second_response.json()
        self.assertEqual(len(data["results"]), 20)

    def test_aucun_message_nest_duplique_entre_les_deux_pages(self):
        self.client.login(username="staff_pagination", password="MotDePasseSolide123")
        first_response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation.id])
        )
        first_data = first_response.json()
        first_ids = {m["id"] for m in first_data["results"]}

        second_response = self.client.get(first_data["next"])
        second_ids = {m["id"] for m in second_response.json()["results"]}

        # Aucun chevauchement entre les deux pages.
        self.assertEqual(first_ids & second_ids, set())
        # Ensemble, on retrouve bien les 50 messages.
        self.assertEqual(len(first_ids | second_ids), 50)

    def test_messages_sont_ordonnes_du_plus_recent_au_plus_ancien(self):
        self.client.login(username="staff_pagination", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("chat:api_conversation_history", args=[self.conversation.id])
        )
        results = response.json()["results"]
        contents = [r["content"] for r in results]
        # Le tout dernier message cree (numero 49) doit apparaitre en premier.
        self.assertEqual(contents[0], "Message numero 49")
