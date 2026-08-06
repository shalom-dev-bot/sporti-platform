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
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        help_text="Photo de profil personnalisee, choisie par l'utilisateur.",
    )
    phone_number = models.CharField(max_length=30, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.get_full_name() or self.email or self.username

    @property
    def display_avatar_url(self):
        """Priorite : photo perso uploadee, puis avatar Google, sinon rien
        (le template affiche alors les initiales)."""
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
        return ""


class PushSubscription(models.Model):
    """Abonnement push d'un utilisateur, cree par son navigateur. Un meme
    utilisateur peut avoir plusieurs abonnements (plusieurs appareils)."""

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh_key = models.CharField(max_length=255)
    auth_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Abonnement push"
        verbose_name_plural = "Abonnements push"

    def __str__(self):
        return f"Abonnement push de {self.user}"
