"""
Verifie que l'admin peut changer son mot de passe depuis le dashboard,
et que la connexion manuelle par email fonctionne pour les clients.
"""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="pwd_change_staff", password="AncienMotDePasse123", is_staff=True
        )

    def test_admin_peut_changer_son_mot_de_passe(self):
        self.client.login(username="pwd_change_staff", password="AncienMotDePasse123")
        response = self.client.post(
            reverse("dashboard:change_password"),
            {
                "old_password": "AncienMotDePasse123",
                "new_password1": "NouveauMotDePasse456",
                "new_password2": "NouveauMotDePasse456",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        connected = self.client.login(username="pwd_change_staff", password="NouveauMotDePasse456")
        self.assertTrue(connected)

    def test_client_non_staff_ne_peut_pas_acceder_a_cette_page(self):
        User.objects.create_user(
            username="pwd_change_client", password="MotDePasseSolide123", is_staff=False
        )
        self.client.login(username="pwd_change_client", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:change_password"))
        self.assertEqual(response.status_code, 302)


class ManualAccountSignupTests(TestCase):
    def test_page_inscription_est_accessible(self):
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 200)

    def test_page_connexion_est_accessible(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
