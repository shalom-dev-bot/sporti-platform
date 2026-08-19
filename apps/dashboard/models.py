"""Petites stats maison pour le tableau de bord admin (pas de service
d'analytics externe -- on compte nous-memes, simplement)."""

from django.conf import settings
from django.db import models


class SiteVisit(models.Model):
    """Une ligne par (jour, client) : un client visitant plusieurs fois
    dans la meme journee, ou naviguant entre plusieurs pages, ne compte
    qu'une seule fois -- "Visites aujourd'hui" est donc un nombre de
    clients distincts, pas un nombre de requetes. Le staff (l'admin
    lui-meme qui navigue sur son propre site) n'est jamais compte, voir
    apps.dashboard.middleware.VisitTrackingMiddleware."""

    date = models.DateField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visite du site"
        verbose_name_plural = "Visites du site"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["date", "user"], name="unique_visit_per_user_per_day")
        ]

    def __str__(self):
        return f"{self.date} : {self.user}"
