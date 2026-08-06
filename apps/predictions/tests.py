from django.test import TestCase

from .models import Team


class TeamModelTests(TestCase):
    def test_initials_uses_first_letter_of_two_words(self):
        team = Team.objects.create(name="Paris SG")
        self.assertEqual(team.initials, "PS")

    def test_initials_falls_back_to_first_two_letters(self):
        team = Team.objects.create(name="Barcelona")
        self.assertEqual(team.initials, "BA")
