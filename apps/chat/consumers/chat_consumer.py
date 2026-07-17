"""
Consumer WebSocket du chat prive Client <-> Entreprise.

Securite (regle non negociable) :
- Un client ne rejoint QUE le groupe de SA PROPRE conversation.
- Un membre du staff peut rejoindre la conversation d'un client precis,
  mais uniquement en tant que staff authentifie.
- Aucun utilisateur ne peut rejoindre un groupe qui ne lui appartient pas.

Statuts de message (comme WhatsApp) :
- SENT      : un coche -- le message est enregistre, destinataire absent.
- DELIVERED : deux coches grises -- le destinataire est connecte et l'a recu.
- READ      : deux coches bleues -- le destinataire a ouvert la conversation.

Indicateur de frappe, presence et accuses de lecture sont diffuses aux
AUTRES membres du groupe uniquement -- jamais renvoyes a l'auteur de
l'evenement (comme sur WhatsApp, on ne se notifie pas soi-meme).
"""

from django.utils import timezone

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import Conversation, Message

_active_connections = {}


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")

        if conversation_id is None:
            if user.is_staff:
                await self.close(code=4003)
                return
            self.conversation = await self._get_or_create_own_conversation(user)
        else:
            if not user.is_staff:
                await self.close(code=4003)
                return
            self.conversation = await self._get_conversation_or_none(conversation_id)
            if self.conversation is None:
                await self.close(code=4004)
                return

        self.group_name = f"conversation_{self.conversation.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        _active_connections.setdefault(self.group_name, set()).add(user.id)

        await self._set_online_status(user, True)
        await self._mark_as_delivered(self.conversation, user)
        updated_ids = await self._mark_as_read(self.conversation, user)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.update",
                "payload": {"user_id": user.id, "is_online": True},
                "origin_channel": self.channel_name,
            },
        )

        if updated_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "read.receipt",
                    "payload": {"message_ids": updated_ids, "status": "read"},
                    "origin_channel": self.channel_name,
                },
            )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            user = self.scope["user"]

            connections = _active_connections.get(self.group_name, set())
            connections.discard(user.id)

            await self._set_online_status(user, False)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.update",
                    "payload": {"user_id": user.id, "is_online": False},
                    "origin_channel": self.channel_name,
                },
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type", "message")

        if message_type == "typing":
            await self._handle_typing(content)
            return

        text = (content.get("message") or "").strip()
        if not text:
            return

        user = self.scope["user"]
        recipient_connected = self._is_other_party_connected(user)
        initial_status = Message.Status.DELIVERED if recipient_connected else Message.Status.SENT

        message = await self._save_message(self.conversation, user, text, initial_status)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "payload": {
                    "id": message.id,
                    "sender_id": user.id,
                    "sender_name": str(user),
                    "is_staff": user.is_staff,
                    "content": message.content,
                    "status": message.status,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def _handle_typing(self, content):
        user = self.scope["user"]
        is_typing = bool(content.get("is_typing", False))

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing.update",
                "payload": {
                    "user_id": user.id,
                    "sender_name": str(user),
                    "is_typing": is_typing,
                },
                "origin_channel": self.channel_name,
            },
        )

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def presence_update(self, event):
        if event.get("origin_channel") == self.channel_name:
            return
        await self.send_json({"type": "presence", **event["payload"]})

    async def read_receipt(self, event):
        if event.get("origin_channel") == self.channel_name:
            return
        await self.send_json({"type": "read_receipt", **event["payload"]})

    async def typing_update(self, event):
        if event.get("origin_channel") == self.channel_name:
            return
        await self.send_json({"type": "typing", **event["payload"]})

    def _is_other_party_connected(self, sender):
        connections = _active_connections.get(self.group_name, set())
        others = connections - {sender.id}
        return len(others) > 0

    @sync_to_async
    def _get_or_create_own_conversation(self, user):
        conversation, _ = Conversation.objects.get_or_create(client=user)
        return conversation

    @sync_to_async
    def _get_conversation_or_none(self, conversation_id):
        return Conversation.objects.filter(id=conversation_id).first()

    @sync_to_async
    def _save_message(self, conversation, sender, text, initial_status):
        return Message.objects.create(
            conversation=conversation, sender=sender, content=text, status=initial_status
        )

    @sync_to_async
    def _set_online_status(self, user, is_online):
        user.is_online = is_online
        user.last_seen_at = timezone.now()
        user.save(update_fields=["is_online", "last_seen_at"])

    @sync_to_async
    def _mark_as_delivered(self, conversation, reader):
        conversation.messages.exclude(sender=reader).filter(status=Message.Status.SENT).update(
            status=Message.Status.DELIVERED
        )

    @sync_to_async
    def _mark_as_read(self, conversation, reader):
        qs = conversation.messages.exclude(sender=reader).exclude(status=Message.Status.READ)
        ids = list(qs.values_list("id", flat=True))
        qs.update(status=Message.Status.READ)
        return ids
