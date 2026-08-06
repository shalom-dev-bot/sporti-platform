"""
Modeles du module Pronostics : une Equipe (avec logo), un Evenement
(un match entre deux equipes) et un Pronostic (le choix de l'admin sur
cet evenement, avec analyse et lien vers la plateforme de paris).
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Team(models.Model):
    """Une equipe/club, reutilisable entre plusieurs evenements. Le logo
    est optionnel : si absent, l'affichage genere un badge avec les
    initiales du nom (comme un avatar par defaut)."""

    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="teams/", blank=True, null=True)
    logo_url = models.URLField(
        blank=True,
        verbose_name="Logo (URL externe)",
        help_text="Rempli automatiquement lors d'un import API-Football.",
    )
    api_football_id = models.PositiveIntegerField(blank=True, null=True, unique=True, db_index=True)

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_logo_url(self):
        """Priorite : logo uploade a la main, puis logo recupere via
        l'import API-Football, sinon rien (le template affiche alors
        les initiales)."""
        if self.logo:
            return self.logo.url
        if self.logo_url:
            return self.logo_url
        return ""

    @property
    def initials(self):
        """Deux lettres representatives, utilisees quand aucun logo n'est
        disponible (badge de secours cote client)."""
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.name[:2].upper()


class Event(models.Model):
    """Un evenement sportif (match) entre deux equipes, a une date/heure
    et dans une competition donnee."""

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_events")
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_events")
    competition = models.CharField(max_length=150)
    sport = models.CharField(max_length=50, default="Football")
    kickoff_at = models.DateTimeField(verbose_name="Date et heure du match")
    api_football_id = models.PositiveIntegerField(blank=True, null=True, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evenement"
        verbose_name_plural = "Evenements"
        ordering = ["-kickoff_at"]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} -- {self.kickoff_at:%d/%m/%Y %H:%M}"


class Prediction(models.Model):
    """Le pronostic de l'admin sur un evenement precis, avec une analyse
    optionnelle et un lien vers la plateforme de paris recommandee."""

    class Result(models.TextChoices):
        PENDING = "pending", "En attente"
        WON = "won", "Gagne"
        LOST = "lost", "Perdu"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="predictions")
    pick = models.CharField(max_length=200, verbose_name="Pronostic (ex: 'Equipe A gagne')")
    analysis = models.TextField(blank=True, verbose_name="Analyse detaillee")
    odds = models.CharField(max_length=20, blank=True, verbose_name="Cote")
    external_link = models.ForeignKey(
        "company.ExternalLink",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="predictions",
        verbose_name="Plateforme de paris recommandee",
    )
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING)
    confidence = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Confiance (%)",
        help_text="Niveau de confiance affiche aux clients (0 a 100, optionnel).",
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Match phare",
        help_text="Mis en avant dans l'onglet 'Top matchs' cote client.",
    )
    is_published = models.BooleanField(default=True, verbose_name="Visible par les clients")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pronostic"
        verbose_name_plural = "Pronostics"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} -- {self.pick}"
