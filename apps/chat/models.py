"""
Coeur du chat prive Client <-> Entreprise.

Regle non negociable : une Conversation appartient a un seul client. Aucun
acces croise n'est possible entre clients -- chaque requete et chaque
connexion WebSocket doivent verifier la propriete de la conversation avant
tout acces.
"""

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Fil de discussion prive entre un client et l'entreprise."""

    client = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation",
        help_text="Un client ne possede qu'une seule conversation avec l'entreprise.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation avec {self.client}"


class Message(models.Model):
    """Message texte, image ou document au sein d'une conversation."""

    class Status(models.TextChoices):
        SENT = "sent", "Envoye"
        DELIVERED = "delivered", "Distribue"
        READ = "read", "Lu"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.conversation_id}] {self.sender}: {self.content[:30]}"


class Attachment(models.Model):
    """Piece jointe (image ou document) liee a un message."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField(help_text="Taille en octets")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Piece jointe"
        verbose_name_plural = "Pieces jointes"

    def __str__(self):
        return self.file_name


class MessageReaction(models.Model):
    """Reaction emoji d'un utilisateur sur un message."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reaction"
        verbose_name_plural = "Reactions"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user", "emoji"], name="unique_reaction_per_user"
            )
        ]
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