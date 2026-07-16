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
        ]


class ConversationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.__str__", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "client",
            "client_name",
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
