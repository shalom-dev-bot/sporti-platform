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
