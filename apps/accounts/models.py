"""
Modele utilisateur personnalise.

Un meme modele sert pour les deux profils de la plateforme :
- is_staff=True  -> compte administrateur (entreprise), email + mot de passe (+2FA)
- is_staff=False -> client, connexion via Google OAuth en priorite
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Utilisateur SPORTI : client ou membre de l'entreprise."""

    avatar_url = models.URLField(
        blank=True,
        help_text="Photo de profil recuperee automatiquement depuis Google.",
    )
    phone_number = models.CharField(max_length=30, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.get_full_name() or self.email or self.username
