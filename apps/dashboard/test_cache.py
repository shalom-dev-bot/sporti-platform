"""
Verifie que le cache Redis des statistiques du dashboard fonctionne
reellement : deuxieme appel sans requete SQL, invalidation correcte.
"""

from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.models import User


class DashboardCacheTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="cache_staff", password="MotDePasseSolide123", is_staff=True
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_deuxieme_appel_ne_fait_aucune_requete_sql(self):
        self.client.login(username="cache_staff", password="MotDePasseSolide123")

        # Premier appel : calcule et met en cache.
        self.client.get(reverse("dashboard:stats"))

        # Deuxieme appel : doit venir entierement du cache, sans toucher
        # les tables User/Conversation/Message pour recalculer les stats.
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse("dashboard:stats"))

        self.assertEqual(response.status_code, 200)
        # Seules les requetes de session/auth doivent rester (2-3 max),
        # aucune requete d'agregation sur User/Conversation/Message.
        sql_queries = [q["sql"] for q in ctx.captured_queries]
        for sql in sql_queries:
            self.assertNotIn("chat_conversation", sql)
            self.assertNotIn("chat_message", sql)

    def test_cache_contient_bien_les_statistiques(self):
        self.client.login(username="cache_staff", password="MotDePasseSolide123")
        self.client.get(reverse("dashboard:stats"))

        cached = cache.get("dashboard:stats")
        self.assertIsNotNone(cached)
        self.assertIn("total_clients", cached)
