"""
Vue publique (cote client) du module Pronostics. Le CRUD (creation,
edition, suppression) reste gere depuis le dashboard admin
(apps.dashboard.views) -- ce fichier ne contient que l'affichage aux
clients connectes.
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.company.models import CompanyProfile

from .models import Prediction

LIVE_MATCH_WINDOW = timedelta(hours=2)


@login_required(login_url="/")
def predictions_list(request):
    """Liste des pronostics publies, visible par tout client connecte.
    Un membre du staff est renvoye vers son espace de gestion, sauf en
    mode apercu (?apercu=1) -- utilise par le bouton "Voir" cote admin
    pour previsualiser l'ecran exact que voit le client."""
    if request.user.is_staff and not request.GET.get("apercu"):
        return redirect("/gestion/pronostics/")

    active_filter = request.GET.get("filtre", "tous")
    predictions = Prediction.objects.filter(is_published=True).select_related(
        "event", "event__home_team", "event__away_team", "external_link"
    )

    now = timezone.now()
    today = timezone.localdate()

    if active_filter == "historique":
        # Un match reste dans "Live" tant qu'il est dans la fenetre
        # estimee de match en cours -- il ne bascule en historique
        # qu'une fois cette fenetre depassee.
        predictions = predictions.filter(event__kickoff_at__lt=now - LIVE_MATCH_WINDOW).order_by(
            "-event__kickoff_at"
        )
    else:
        # "Tous" (et les sous-filtres) = pronostics actuels/a venir. Les
        # matchs deja termines (kickoff + fenetre live depassee) restent
        # consultables uniquement via "Historique", sinon ils polluaient
        # le haut de la liste (tri chronologique croissant).
        predictions = predictions.exclude(event__kickoff_at__lt=now - LIVE_MATCH_WINDOW)
        if active_filter == "aujourdhui":
            predictions = predictions.filter(event__kickoff_at__date=today)
        elif active_filter == "top":
            predictions = predictions.filter(is_featured=True)
        elif active_filter == "live":
            # Pas de statut "live" reel remonte par l'API-Football cote
            # client : on estime qu'un match est en cours s'il a commence
            # il y a moins de LIVE_MATCH_WINDOW. Approximatif, mais evite
            # d'attendre un deuxieme appel API a chaque affichage de la liste.
            predictions = predictions.filter(event__kickoff_at__lte=now)
        predictions = predictions.order_by("event__kickoff_at")

    predictions = list(predictions)
    for prediction in predictions:
        kickoff = prediction.event.kickoff_at
        prediction.is_live = kickoff <= now <= kickoff + LIVE_MATCH_WINDOW

    published = Prediction.objects.filter(is_published=True)
    total_count = published.count()
    won_count = published.filter(result=Prediction.Result.WON).count()
    success_rate = round((won_count / total_count) * 100) if total_count else 0
    new_today_count = published.filter(
        event__kickoff_at__date=today,
        event__kickoff_at__gte=now - LIVE_MATCH_WINDOW,
    ).count()

    # "Forme recente" : les N derniers pronostics reellement resolus
    # (gagne/perdu), du plus ancien au plus recent -- jamais de donnees
    # fictives, juste ce qui existe vraiment en base. S'affiche vide tant
    # qu'aucun match n'a ete tranche par l'admin.
    recent_form = list(
        published.exclude(result=Prediction.Result.PENDING)
        .select_related("event__home_team", "event__away_team")
        .order_by("-event__kickoff_at")[:10]
    )
    recent_form.reverse()

    profile, _ = CompanyProfile.objects.get_or_create(pk=1)

    return render(
        request,
        "predictions/list.html",
        {
            "predictions": predictions,
            "active_filter": active_filter,
            "total_count": total_count,
            "won_count": won_count,
            "success_rate": success_rate,
            "new_today_count": new_today_count,
            "active_clients_count": User.objects.filter(is_staff=False, is_active=True).count(),
            "recent_form": recent_form,
            "company": profile,
        },
    )
