from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.company.models import CompanyProfile
from apps.predictions.models import Event, Prediction


def home(request):
    """Page d'accueil publique pour un visiteur, ou ecran de choix
    (hub) une fois le client connecte. Un membre du staff qui atterrit
    ici est renvoye vers son espace de gestion plutot que vers le hub."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("/gestion/")
    if request.user.is_authenticated:
        profile, _ = CompanyProfile.objects.get_or_create(pk=1)
        today = timezone.localdate()
        published = Prediction.objects.filter(is_published=True)
        total_predictions = published.count()
        won_predictions = published.filter(result=Prediction.Result.WON).count()
        success_rate = (
            round((won_predictions / total_predictions) * 100) if total_predictions else 0
        )
        context = {
            "company": profile,
            "new_today_count": published.filter(event__kickoff_at__date=today).count(),
            "total_predictions": total_predictions,
            "won_predictions": won_predictions,
            "success_rate": success_rate,
            "upcoming_events_count": Event.objects.filter(kickoff_at__gte=timezone.now()).count(),
            "active_clients_count": User.objects.filter(is_staff=False, is_active=True).count(),
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
    return render(request, "chat/room.html")


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
