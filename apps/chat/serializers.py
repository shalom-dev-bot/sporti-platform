"""
Serializers DRF pour l'historique du chat.
"""

from rest_framework import serializers

from .models import Attachment, Conversation, Message, MessageReaction


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "file", "file_name", "file_type", "file_size", "uploaded_at"]


class MessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReaction
        fields = ["id", "user", "emoji", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.__str__", read_only=True)
    is_staff = serializers.BooleanField(source="sender.is_staff", read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_name",
            "is_staff",
            "content",
            "status",
            "created_at",
            "attachments",
            "reactions",
            "reply_to",
        ]

    def get_reply_to(self, obj):
        return _reply_to_summary(obj.reply_to)


def _reply_to_summary(message):
    """Petit resume d'un message cite en reponse -- reutilise a la fois
    par le serializer (historique) et par le consumer (temps reel), pour
    que les deux canaux renvoient exactement la meme forme."""
    if message is None:
        return None
    has_attachment = message.attachments.exists()
    return {
        "id": message.id,
        "sender_name": str(message.sender),
        "is_staff": message.sender.is_staff,
        "content": message.content,
        "has_attachment": has_attachment,
    }


class ConversationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.__str__", read_only=True)
    client_is_online = serializers.BooleanField(source="client.is_online", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "client",
            "client_name",
            "client_is_online",
            "created_at",
            "updated_at",
            "is_archived",
            "last_message",
            "unread_count",
        ]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last is None:
            return None
        return {"content": last.content, "created_at": last.created_at, "status": last.status}

    def get_unread_count(self, obj):
        return obj.messages.exclude(status=Message.Status.READ).count()
