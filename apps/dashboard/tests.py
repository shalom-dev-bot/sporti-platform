"""
Tests des vues du dashboard : verifie que seul le staff y accede, et que
les statistiques/listes retournees sont coherentes.
"""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.chat.models import Conversation, Message


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="dash_staff", password="MotDePasseSolide123", is_staff=True
        )
        self.client_user = User.objects.create_user(
            username="dash_client", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.client_user)
        Message.objects.create(
            conversation=self.conversation, sender=self.client_user, content="Bonjour"
        )

    def test_staff_accede_a_la_vue_densemble(self):
        self.client.login(username="dash_staff", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:stats"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord")

    def test_client_ne_peut_pas_acceder_a_la_vue_densemble(self):
        self.client.login(username="dash_client", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:stats"))
        self.assertEqual(response.status_code, 302)

    def test_staff_voit_la_liste_des_conversations(self):
        self.client.login(username="dash_staff", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:conversations_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dash_client")

    def test_staff_peut_ouvrir_une_conversation_precise(self):
        self.client.login(username="dash_staff", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("dashboard:conversation_detail", args=[self.conversation.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bonjour")

    def test_client_ne_peut_pas_ouvrir_une_conversation_via_dashboard(self):
        self.client.login(username="dash_client", password="MotDePasseSolide123")
        response = self.client.get(
            reverse("dashboard:conversation_detail", args=[self.conversation.id])
        )
        self.assertEqual(response.status_code, 302)
