"""
Tests des champs multilingues du contenu admin (description entreprise,
message d'accueil) : verifie l'affichage dans la bonne langue et le
repli automatique sur le francais si la traduction anglaise est vide.
"""

from django.test import TestCase

from ..models import CompanyProfile, WelcomeMessage


class MultilingualContentTests(TestCase):
    def test_description_renvoie_francais_par_defaut(self):
        profile = CompanyProfile.objects.create(
            name="SPORTI", description_fr="Description en francais"
        )
        self.assertEqual(profile.get_description("fr"), "Description en francais")

    def test_description_renvoie_anglais_si_rempli(self):
        profile = CompanyProfile.objects.create(
            name="SPORTI",
            description_fr="Description en francais",
            description_en="Description in English",
        )
        self.assertEqual(profile.get_description("en"), "Description in English")

    def test_description_replie_sur_francais_si_anglais_vide(self):
        profile = CompanyProfile.objects.create(
            name="SPORTI", description_fr="Description en francais", description_en=""
        )
        self.assertEqual(profile.get_description("en"), "Description en francais")

    def test_message_accueil_replie_sur_francais_si_anglais_vide(self):
        message = WelcomeMessage.objects.create(text_fr="Bienvenue !", text_en="")
        self.assertEqual(message.get_text("en"), "Bienvenue !")

    def test_message_accueil_renvoie_anglais_si_rempli(self):
        message = WelcomeMessage.objects.create(text_fr="Bienvenue !", text_en="Welcome!")
        self.assertEqual(message.get_text("en"), "Welcome!")
