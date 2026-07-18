"""
Vue API : enregistre l'abonnement push d'un utilisateur (cree par le
navigateur via la Push API), pour pouvoir lui envoyer des notifications
meme lorsque l'application est fermee.
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushSubscription


class PushSubscribeView(APIView):
    """Enregistre ou met a jour un abonnement push pour l'utilisateur connecte."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")
        keys = request.data.get("keys", {})
        p256dh = keys.get("p256dh")
        auth = keys.get("auth")

        if not all([endpoint, p256dh, auth]):
            return Response(
                {"detail": "Donnees d'abonnement incompletes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh_key": p256dh, "auth_key": auth},
        )
        return Response({"detail": "Abonnement enregistre."}, status=status.HTTP_201_CREATED)
