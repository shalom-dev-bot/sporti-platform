"""
Consumer WebSocket du chat prive.

Securite : a la connexion, l'utilisateur ne rejoint QUE le groupe
correspondant a SA PROPRE conversation. Aucun autre groupe n'est accessible,
ce qui garantit qu'aucun client ne peut recevoir les messages d'un autre.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import Conversation


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.conversation = await self._get_or_create_conversation(user)
        self.group_name = f"conversation_{self.conversation.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "payload": content},
        )

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def _get_or_create_conversation(self, user):
        from asgiref.sync import sync_to_async

        get_or_create = sync_to_async(Conversation.objects.get_or_create)
        conversation, _ = await get_or_create(client=user)
        return conversation
