"""Suit la derniere activite des membres du staff, pour savoir si
l'admin est present sur la plateforme (dashboard, chat, n'importe
quelle page) -- pas seulement lorsqu'il a une conversation ouverte."""

from django.utils import timezone

_THROTTLE_SECONDS = 20


class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            now = timezone.now()
            if (
                not user.last_seen_at
                or (now - user.last_seen_at).total_seconds() > _THROTTLE_SECONDS
            ):
                user.last_seen_at = now
                user.save(update_fields=["last_seen_at"])
        return self.get_response(request)
