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
    from django.db import models

class AppSettings(models.Model):
    welcome_message = models.TextField(
        default="Bienvenue sur SPORTI ! Nous sommes ravis de vous compter parmi nous. Rejoignez nos canaux officiels pour toute question ou mise à jour."
    )
    telegram_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="Lien Telegram du gestionnaire"
    )
    whatsapp_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="Lien de la chaîne WhatsApp"
    )

    class Meta:
        verbose_name = "Configuration de l'application"
        verbose_name_plural = "Configurations de l'application"

    def __str__(self):
        return "Configuration Générale SPORTI"

    @classmethod
    def get_settings(cls):
        """Récupère l'unique instance de configuration ou en crée une par défaut."""
        settings, _ = cls.objects.get_or_create(id=1)
        return settings
