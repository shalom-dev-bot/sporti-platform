"""
Vue publique (cote client) du module Pronostics. Le CRUD (creation,
edition, suppression) reste gere depuis le dashboard admin
(apps.dashboard.views) -- ce fichier ne contient que l'affichage aux
clients connectes.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Prediction


@login_required(login_url="/")
def predictions_list(request):
    """Liste des pronostics publies, visible par tout client connecte.
    Un membre du staff est renvoye vers son espace de gestion."""
    if request.user.is_staff:
        return redirect("/gestion/pronostics/")

    active_filter = request.GET.get("filtre", "tous")
    predictions = Prediction.objects.filter(is_published=True).select_related(
        "event", "event__home_team", "event__away_team", "external_link"
    )

    if active_filter == "aujourdhui":
        today = timezone.localdate()
        predictions = predictions.filter(event__kickoff_at__date=today)
    elif active_filter == "top":
        predictions = predictions.filter(is_featured=True)

    predictions = predictions.order_by("event__kickoff_at")

    total_count = Prediction.objects.filter(is_published=True).count()
    won_count = Prediction.objects.filter(is_published=True, result=Prediction.Result.WON).count()

    return render(
        request,
        "predictions/list.html",
        {
            "predictions": predictions,
            "active_filter": active_filter,
            "total_count": total_count,
            "won_count": won_count,
        },
    )
