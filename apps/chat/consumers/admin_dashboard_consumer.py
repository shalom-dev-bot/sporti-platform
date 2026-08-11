"""Canal WebSocket global pour l'espace de gestion : permet a la liste des
conversations (barre laterale desktop, page Conversations) de se remettre
a jour toute seule des qu'un message arrive -- dans n'importe quelle
conversation -- sans devoir rafraichir la page, comme sur WhatsApp Web.

Aucune donnee sensible n'y transite : seulement de quoi rafraichir une
ligne de la liste (nom du client, apercu du dernier message, heure).
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer

ADMIN_DASHBOARD_GROUP = "admin_dashboard"


class AdminDashboardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or not user.is_staff:
            await self.close(code=4003)
            return
        await self.channel_layer.group_add(ADMIN_DASHBOARD_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(ADMIN_DASHBOARD_GROUP, self.channel_name)

    async def conversation_updated(self, event):
        await self.send_json(event["payload"])
