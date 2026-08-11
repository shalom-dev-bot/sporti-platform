"""Compte une visite par requete de page (hors static/media/websocket),
pour alimenter la stat "Visites aujourd'hui" du tableau de bord admin."""

from django.db.models import F
from django.utils import timezone

from .models import SiteVisit

_SKIP_PREFIXES = ("/static/", "/media/", "/ws/", "/service-worker.js")


class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not any(request.path.startswith(p) for p in _SKIP_PREFIXES):
            today = timezone.localdate()
            updated = SiteVisit.objects.filter(date=today).update(count=F("count") + 1)
            if not updated:
                SiteVisit.objects.get_or_create(date=today, defaults={"count": 1})
        return self.get_response(request)
