"""
Verifie que le rate limiting fonctionne reellement : au-dela de la limite
autorisee, les requetes supplementaires sont bloquees.
"""

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class LoginRateLimitTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="ratelimit_staff", password="MotDePasseSolide123", is_staff=True
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_6eme_tentative_de_connexion_est_bloquee(self):
        """La limite est de 5 tentatives par minute et par IP -- la
        6eme doit etre refusee, meme avec les bons identifiants."""
        url = reverse("dashboard:login")

        for i in range(5):
            response = self.client.post(
                url, {"username": "ratelimit_staff", "password": "mauvais_mot_de_passe"}
            )
            # Les 5 premieres passent (mauvais mdp -- statut 200).
            self.assertNotEqual(response.status_code, 403)

        # La 6eme tentative doit etre bloquee par le rate limiting.
        response = self.client.post(
            url, {"username": "ratelimit_staff", "password": "MotDePasseSolide123"}
        )
        self.assertEqual(response.status_code, 403)


class UploadRateLimitTests(TestCase):
    def setUp(self):
        from apps.chat.models import Conversation

        self.client_user = User.objects.create_user(
            username="ratelimit_upload_client", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.client_user)
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_21eme_upload_est_bloque(self):
        """La limite est de 20 uploads par minute et par utilisateur --
        le 21eme doit etre refuse."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.urls import reverse

        self.client.login(username="ratelimit_upload_client", password="MotDePasseSolide123")
        url = reverse("chat:api_attachment_upload", args=[self.conversation.id])

        for i in range(20):
            fichier = SimpleUploadedFile(f"test{i}.mp3", b"contenu", content_type="audio/mpeg")
            response = self.client.post(url, {"file": fichier})
            self.assertNotEqual(response.status_code, 403)

        fichier_21 = SimpleUploadedFile("test21.mp3", b"contenu", content_type="audio/mpeg")
        response = self.client.post(url, {"file": fichier_21})
        self.assertEqual(response.status_code, 403)
