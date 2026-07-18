"""
Envoi de notifications push via la Web Push API (pywebpush).
Utilise depuis le consumer WebSocket quand le destinataire d'un message
n'est pas connecte au moment de l'envoi.
"""

import json

from django.conf import settings

from pywebpush import WebPushException, webpush


def send_push_notification(user, title, body, url="/"):
    """Envoie une notification push a TOUS les appareils abonnes de
    l'utilisateur. Supprime automatiquement les abonnements expires."""
    subscriptions = user.push_subscriptions.all()

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_key,
                    },
                },
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
            )
        except WebPushException as exc:
            # Abonnement expire ou invalide : on le supprime pour ne plus
            # essayer d'y envoyer des notifications inutilement.
            if exc.response is not None and exc.response.status_code in (404, 410):
                subscription.delete()
