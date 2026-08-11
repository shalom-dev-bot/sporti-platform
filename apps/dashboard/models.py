"""Petites stats maison pour le tableau de bord admin (pas de service
d'analytics externe -- on compte nous-memes, simplement)."""

from django.db import models


class SiteVisit(models.Model):
    """Un compteur de visites par jour, incremente par
    apps.dashboard.middleware.VisitTrackingMiddleware."""

    date = models.DateField(unique=True, db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Visite du site"
        verbose_name_plural = "Visites du site"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} : {self.count} visites"
