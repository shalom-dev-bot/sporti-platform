from datetime import timedelta

from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.company.models import CompanyProfile
from apps.predictions.models import Prediction

ADMIN_ONLINE_WINDOW = timedelta(minutes=2)
LIVE_MATCH_WINDOW = timedelta(hours=2)


def _is_admin_online():
    """Un membre du staff est considere "en ligne" s'il a ete actif sur
    la plateforme (n'importe quelle page, pas seulement une conversation)
    dans la fenetre recente -- voir apps.accounts.middleware."""
    return User.objects.filter(
        is_staff=True, last_seen_at__gte=timezone.now() - ADMIN_ONLINE_WINDOW
    ).exists()


def home(request):
    """Page d'accueil publique pour un visiteur, ou ecran de choix
    (hub) une fois le client connecte. Un membre du staff qui atterrit
    ici est renvoye vers son espace de gestion plutot que vers le hub."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("/gestion/")
    if request.user.is_authenticated:
        profile, _ = CompanyProfile.objects.get_or_create(pk=1)
        now = timezone.now()
        today = timezone.localdate()
        published = Prediction.objects.filter(is_published=True)
        total_predictions = published.count()
        won_predictions = published.filter(result=Prediction.Result.WON).count()
        success_rate = (
            round((won_predictions / total_predictions) * 100) if total_predictions else 0
        )
        # "Disponible aujourd'hui" = publie, prevu aujourd'hui, et pas
        # encore expire (coup d'envoi + fenetre live pas depasse) -- sinon
        # le compteur restait fige toute la journee meme apres la fin du match.
        available_today_count = published.filter(
            event__kickoff_at__date=today,
            event__kickoff_at__gte=now - LIVE_MATCH_WINDOW,
        ).count()
        context = {
            "company": profile,
            "new_today_count": available_today_count,
            "total_predictions": total_predictions,
            "won_predictions": won_predictions,
            "success_rate": success_rate,
            "active_clients_count": User.objects.filter(is_staff=False, is_active=True).count(),
            "admin_online": _is_admin_online(),
        }
        return render(request, "chat/hub.html", context)

    published = Prediction.objects.filter(is_published=True)
    total_predictions = published.count()
    won_predictions = published.filter(result=Prediction.Result.WON).count()
    public_context = {
        "active_members_count": User.objects.filter(is_staff=False, is_active=True).count(),
        "success_rate": (
            round((won_predictions / total_predictions) * 100) if total_predictions else 0
        ),
    }
    return render(request, "chat/home.html", public_context)


def chat_room(request):
    """Le chat prive lui-meme, accessible uniquement aux clients connectes
    (choisi depuis le hub)."""
    if not request.user.is_authenticated:
        return redirect("chat:home")
    if request.user.is_staff:
        return redirect("/gestion/")
    return render(request, "chat/room.html", {"admin_online": _is_admin_online()})


def service_worker(request):
    from django.conf import settings
    from django.http import HttpResponse

    with open(settings.BASE_DIR / "static" / "service-worker.js", "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="application/javascript")


def offline(request):
    """Page de secours affichee par le service worker quand le
    navigateur est hors ligne et que la page demandee n'est pas en cache."""
    return render(request, "offline/offline.html")
