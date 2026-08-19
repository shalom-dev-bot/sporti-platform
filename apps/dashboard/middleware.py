"""Compte un client distinct par jour (hors static/media/websocket/API),
pour alimenter la stat "Visites aujourd'hui" du tableau de bord admin.

Ne compte que les clients authentifies et non-staff : l'admin qui navigue
sur son propre site ne doit jamais gonfler ses propres statistiques, et
un client qui revient plusieurs fois (ou dont le JS fait des appels
API/AJAX en arriere-plan) ne doit compter qu'une fois par jour, pas une
fois par requete -- voir apps.dashboard.models.SiteVisit."""

from django.utils import timezone

from .models import SiteVisit

_SKIP_PREFIXES = ("/static/", "/media/", "/ws/", "/service-worker.js")


def _is_trackable_path(path):
    # Certaines API (chat, notamment) sont dans i18n_patterns et recoivent
    # donc un prefixe de langue ("/fr/api/..."), donc un simple startswith
    # sur "/api/" ne les detecterait jamais -- on cherche le segment
    # n'importe ou dans le chemin a la place.
    if any(path.startswith(p) for p in _SKIP_PREFIXES):
        return False
    if "/api/" in path:
        return False
    return True


class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_staff
            and _is_trackable_path(request.path)
        ):
            SiteVisit.objects.get_or_create(date=timezone.localdate(), user=user)
        return self.get_response(request)
