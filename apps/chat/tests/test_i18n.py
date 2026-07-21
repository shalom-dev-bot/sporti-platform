"""
Verifie que le systeme i18n fonctionne : la page d'accueil repond bien
en francais et en anglais selon le prefixe d'URL.
"""

from django.test import TestCase


class I18nTests(TestCase):
    def test_page_accueil_en_francais(self):
        response = self.client.get("/fr/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Se connecter avec Google")

    def test_page_accueil_en_anglais(self):
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in with Google")


class OfflinePageTests(TestCase):
    def test_page_offline_est_accessible(self):
        response = self.client.get("/offline/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hors ligne")
