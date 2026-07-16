"""
Consumer WebSocket du chat prive Client <-> Entreprise.

Securite (regle non negociable) :
- Un client ne rejoint QUE le groupe de SA PROPRE conversation.
- Un membre du staff (entreprise) peut rejoindre la conversation d'un
  client precis, mais uniquement en tant que staff authentifie.
- Aucun utilisateur ne peut rejoindre un groupe qui ne lui appartient pas.
"""

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")

        if conversation_id is None:
            # Connexion cote client : sa propre conversation, creee si besoin.
            if user.is_staff:
                # Un membre du staff doit toujours preciser une conversation.
                await self.close(code=4003)
                return
            self.conversation = await self._get_or_create_own_conversation(user)
        else:
            # Connexion cote entreprise : doit etre staff pour consulter
            # la conversation d'un client precis.
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

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = (content.get("message") or "").strip()
        if not text:
            return

        user = self.scope["user"]
        message = await self._save_message(self.conversation, user, text)

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

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    @sync_to_async
    def _get_or_create_own_conversation(self, user):
        conversation, _ = Conversation.objects.get_or_create(client=user)
        return conversation

    @sync_to_async
    def _get_conversation_or_none(self, conversation_id):
        return Conversation.objects.filter(id=conversation_id).first()

    @sync_to_async
    def _save_message(self, conversation, sender, text):
        return Message.objects.create(conversation=conversation, sender=sender, content=text)
