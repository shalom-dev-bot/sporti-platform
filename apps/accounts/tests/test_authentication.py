"""
Tests d'authentification.

Verifie que :
- un utilisateur peut se connecter avec les bons identifiants ;
- une connexion avec un mauvais mot de passe est refusee ;
- un client (non-staff) ne peut PAS acceder a l'espace de gestion ;
- un membre du staff peut acceder a l'espace de gestion.
"""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="admin_sporti",
            password="MotDePasseSolide123",
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username="client_test",
            password="MotDePasseSolide123",
            is_staff=False,
        )

    def test_connexion_reussie_avec_bons_identifiants(self):
        """Un utilisateur existant doit pouvoir se connecter avec le bon mot de passe."""
        logged_in = self.client.login(username="admin_sporti", password="MotDePasseSolide123")
        self.assertTrue(logged_in)

    def test_connexion_refusee_avec_mauvais_mot_de_passe(self):
        """Un mauvais mot de passe ne doit jamais permettre la connexion."""
        logged_in = self.client.login(username="admin_sporti", password="mauvais_mot_de_passe")
        self.assertFalse(logged_in)

    def test_client_non_staff_ne_peut_pas_acceder_au_dashboard(self):
        """Regle de securite centrale : un client ne doit jamais entrer dans /gestion/."""
        self.client.login(username="client_test", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:stats"))
        # Doit rediriger vers la page de connexion, pas afficher le dashboard.
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gestion/connexion/", response.url)

    def test_staff_peut_acceder_au_dashboard(self):
        """Un membre du staff (entreprise) doit pouvoir entrer dans /gestion/."""
        self.client.login(username="admin_sporti", password="MotDePasseSolide123")
        response = self.client.get(reverse("dashboard:stats"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord SPORTI")

    def test_visiteur_non_connecte_redirige_vers_connexion(self):
        """Un visiteur non authentifie ne doit jamais voir le dashboard."""
        response = self.client.get(reverse("dashboard:stats"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gestion/connexion/", response.url)
