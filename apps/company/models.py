"""
Modeles gerant l'identite de l'entreprise, son message d'accueil et ses
liens externes -- entierement pilotables depuis le tableau de bord admin.
"""
from django.db import models


class CompanyProfile(models.Model):
    """Profil unique de l'entreprise (singleton applicatif)."""

    name = models.CharField(max_length=150, default="SPORTI")
    logo = models.ImageField(upload_to="company/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="company/", blank=True, null=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Profil entreprise"
        verbose_name_plural = "Profil entreprise"

    def __str__(self):
        return self.name


class WelcomeMessage(models.Model):
    """Message d'accueil affiche aux nouveaux visiteurs, avec audio/video
    optionnels, activables independamment."""

    text_fr = models.TextField()
    text_en = models.TextField(blank=True)
    audio_file = models.FileField(upload_to="welcome/audio/", blank=True, null=True)
    video_file = models.FileField(upload_to="welcome/video/", blank=True, null=True)
    is_text_enabled = models.BooleanField(default=True)
    is_audio_enabled = models.BooleanField(default=False)
    is_video_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Message d'accueil"
        verbose_name_plural = "Message d'accueil"

    def __str__(self):
        return "Message d'accueil"


class ExternalLink(models.Model):
    """Lien de contact externe (WhatsApp, Telegram, Facebook, Instagram...)."""

    class Platform(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        TELEGRAM = "telegram", "Telegram"
        FACEBOOK = "facebook", "Facebook Messenger"
        INSTAGRAM = "instagram", "Instagram"
        OTHER = "other", "Autre"

    platform = models.CharField(max_length=20, choices=Platform.choices)
    label = models.CharField(max_length=100, blank=True)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Lien externe"
        verbose_name_plural = "Liens externes"
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_platform_display()} -- {self.url}"
