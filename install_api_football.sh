#!/usr/bin/env bash
set -e
echo "Installation du module API-Football..."

mkdir -p "$(dirname "apps/predictions/models.py")"
cat > apps/predictions/models.py << 'SPORTI_EOF'
"""
Modeles du module Pronostics : une Equipe (avec logo), un Evenement
(un match entre deux equipes) et un Pronostic (le choix de l'admin sur
cet evenement, avec analyse et lien vers la plateforme de paris).
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Team(models.Model):
    """Une equipe/club, reutilisable entre plusieurs evenements. Le logo
    est optionnel : si absent, l'affichage genere un badge avec les
    initiales du nom (comme un avatar par defaut)."""

    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="teams/", blank=True, null=True)
    logo_url = models.URLField(
        blank=True,
        verbose_name="Logo (URL externe)",
        help_text="Rempli automatiquement lors d'un import API-Football.",
    )
    api_football_id = models.PositiveIntegerField(blank=True, null=True, unique=True, db_index=True)

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_logo_url(self):
        """Priorite : logo uploade a la main, puis logo recupere via
        l'import API-Football, sinon rien (le template affiche alors
        les initiales)."""
        if self.logo:
            return self.logo.url
        if self.logo_url:
            return self.logo_url
        return ""

    @property
    def initials(self):
        """Deux lettres representatives, utilisees quand aucun logo n'est
        disponible (badge de secours cote client)."""
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.name[:2].upper()


class Event(models.Model):
    """Un evenement sportif (match) entre deux equipes, a une date/heure
    et dans une competition donnee."""

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_events")
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_events")
    competition = models.CharField(max_length=150)
    sport = models.CharField(max_length=50, default="Football")
    kickoff_at = models.DateTimeField(verbose_name="Date et heure du match")
    api_football_id = models.PositiveIntegerField(blank=True, null=True, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evenement"
        verbose_name_plural = "Evenements"
        ordering = ["-kickoff_at"]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} -- {self.kickoff_at:%d/%m/%Y %H:%M}"


class Prediction(models.Model):
    """Le pronostic de l'admin sur un evenement precis, avec une analyse
    optionnelle et un lien vers la plateforme de paris recommandee."""

    class Result(models.TextChoices):
        PENDING = "pending", "En attente"
        WON = "won", "Gagne"
        LOST = "lost", "Perdu"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="predictions")
    pick = models.CharField(max_length=200, verbose_name="Pronostic (ex: 'Equipe A gagne')")
    analysis = models.TextField(blank=True, verbose_name="Analyse detaillee")
    odds = models.CharField(max_length=20, blank=True, verbose_name="Cote")
    external_link = models.ForeignKey(
        "company.ExternalLink",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="predictions",
        verbose_name="Plateforme de paris recommandee",
    )
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING)
    confidence = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Confiance (%)",
        help_text="Niveau de confiance affiche aux clients (0 a 100, optionnel).",
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Match phare",
        help_text="Mis en avant dans l'onglet 'Top matchs' cote client.",
    )
    is_published = models.BooleanField(default=True, verbose_name="Visible par les clients")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pronostic"
        verbose_name_plural = "Pronostics"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} -- {self.pick}"
SPORTI_EOF
echo "  ecrit: apps/predictions/models.py"

mkdir -p "$(dirname "apps/predictions/api_football.py")"
cat > apps/predictions/api_football.py << 'SPORTI_EOF'
"""
Client pour l'API-Football (v3.football.api-sports.io). Une seule
responsabilite : interroger l'API et renvoyer des donnees Python
simples (dicts), sans toucher a la base de donnees -- l'import en
base se fait dans apps.dashboard.views.

Necessite API_FOOTBALL_KEY dans les settings (voir .env.example).
Compte gratuit sur https://dashboard.api-football.com -- le plan
gratuit est limite en nombre de requetes par jour, donc chaque
recherche admin ne declenche qu'un seul appel API.
"""

from django.conf import settings

import requests

# Quelques competitions populaires pour faciliter la recherche depuis
# le dashboard (id API-Football : nom affiche). Liste volontairement
# courte -- l'admin peut aussi saisir un autre id directement.
POPULAR_LEAGUES = [
    (39, "Premier League (Angleterre)"),
    (61, "Ligue 1 (France)"),
    (140, "La Liga (Espagne)"),
    (135, "Serie A (Italie)"),
    (78, "Bundesliga (Allemagne)"),
    (2, "Ligue des Champions"),
    (3, "Ligue Europa"),
    (848, "Conference League"),
]


class ApiFootballError(Exception):
    """Erreur lors de l'appel a l'API-Football (cle manquante, quota
    depasse, reponse invalide, etc.)."""


def _headers():
    if not settings.API_FOOTBALL_KEY:
        raise ApiFootballError(
            "Aucune cle API-Football configuree (API_FOOTBALL_KEY dans le .env)."
        )
    return {"x-apisports-key": settings.API_FOOTBALL_KEY}


def search_fixtures(date_str, league_id=None, season=None):
    """Recupere les matchs pour une date donnee (YYYY-MM-DD), filtres
    par competition si league_id est fourni. Renvoie une liste de
    dicts normalises, triee par heure de coup d'envoi.

    Leve ApiFootballError si la cle est absente ou si l'appel echoue.
    """
    params = {"date": date_str}
    if league_id:
        params["league"] = league_id
        params["season"] = season or int(date_str[:4])

    try:
        response = requests.get(
            f"{settings.API_FOOTBALL_BASE_URL}/fixtures",
            headers=_headers(),
            params=params,
            timeout=10,
        )
    except requests.RequestException as exc:
        raise ApiFootballError(f"Impossible de contacter l'API-Football : {exc}") from exc

    if response.status_code != 200:
        raise ApiFootballError(f"L'API-Football a repondu avec le code {response.status_code}.")

    payload = response.json()
    errors = payload.get("errors")
    if errors:
        # L'API renvoie parfois un dict, parfois une liste, selon l'erreur.
        message = errors if isinstance(errors, str) else str(errors)
        raise ApiFootballError(f"Erreur API-Football : {message}")

    fixtures = []
    for item in payload.get("response", []):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        if not (fixture.get("id") and home.get("id") and away.get("id")):
            continue

        fixtures.append(
            {
                "api_id": fixture["id"],
                "kickoff_at": fixture.get("date"),
                "status_short": fixture.get("status", {}).get("short", ""),
                "competition": f"{league.get('name', '')} ({league.get('country', '')})".strip(),
                "home_id": home["id"],
                "home_name": home.get("name", ""),
                "home_logo": home.get("logo", ""),
                "away_id": away["id"],
                "away_name": away.get("name", ""),
                "away_logo": away.get("logo", ""),
            }
        )

    fixtures.sort(key=lambda f: f["kickoff_at"] or "")
    return fixtures
SPORTI_EOF
echo "  ecrit: apps/predictions/api_football.py"

mkdir -p "$(dirname "apps/predictions/migrations/0003_event_api_football_id_team_api_football_id_and_more.py")"
cat > apps/predictions/migrations/0003_event_api_football_id_team_api_football_id_and_more.py << 'SPORTI_EOF'
# Generated by Django 5.1.4 on 2026-08-05 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("predictions", "0002_prediction_confidence_prediction_is_featured"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="api_football_id",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="team",
            name="api_football_id",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="team",
            name="logo_url",
            field=models.URLField(
                blank=True,
                help_text="Rempli automatiquement lors d'un import API-Football.",
                verbose_name="Logo (URL externe)",
            ),
        ),
    ]
SPORTI_EOF
echo "  ecrit: apps/predictions/migrations/0003_event_api_football_id_team_api_football_id_and_more.py"

mkdir -p "$(dirname "apps/dashboard/views.py")"
cat > apps/dashboard/views.py << 'SPORTI_EOF'
"""
Espace de gestion de l'entreprise -- interface personnalisee SPORTI,
distincte de l'admin Django par defaut (reserve aux developpeurs sur /admin/).
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.company.forms import CompanyProfileForm, ExternalLinkForm, WelcomeMessageForm
from apps.company.models import CompanyProfile, ExternalLink, WelcomeMessage
from apps.predictions import api_football
from apps.predictions.models import Event, Prediction, Team

from .forms import AdminPasswordChangeForm, AdminUsernameForm, EventForm, PredictionForm, TeamForm

CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"
CACHE_TTL_DASHBOARD_STATS = 60  # secondes : assez court pour rester a jour,
# assez long pour eviter de recalculer a chaque chargement de page.


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/gestion/conversations/"


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def dashboard_home(request):
    """Vue d'ensemble : statistiques cles et evolution du nombre de clients.
    Mise en cache Redis : les statistiques ne sont recalculees qu'une fois
    par minute maximum, meme si plusieurs admins consultent la page en
    meme temps."""
    context = cache.get(CACHE_KEY_DASHBOARD_STATS)
    if context is not None:
        return render(request, "dashboard/home.html", context)

    total_clients = User.objects.filter(is_staff=False).count()
    total_conversations = Conversation.objects.count()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = Message.objects.filter(created_at__gte=today_start).count()

    unread_conversations = (
        Conversation.objects.filter(messages__sender__is_staff=False)
        .exclude(messages__status=Message.Status.READ)
        .distinct()
        .count()
    )

    twelve_months_ago = timezone.now() - timedelta(days=365)
    growth_qs = (
        User.objects.filter(is_staff=False, date_joined__gte=twelve_months_ago)
        .annotate(month=TruncMonth("date_joined"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    growth_labels = [row["month"].strftime("%b %Y") for row in growth_qs]
    growth_values = [row["count"] for row in growth_qs]

    context = {
        "total_clients": total_clients,
        "total_conversations": total_conversations,
        "messages_today": messages_today,
        "unread_conversations": unread_conversations,
        "growth_labels": growth_labels,
        "growth_values": growth_values,
    }
    cache.set(CACHE_KEY_DASHBOARD_STATS, context, CACHE_TTL_DASHBOARD_STATS)
    return render(request, "dashboard/home.html", context)


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversations_list(request):
    """Liste complete et organisee des conversations, triee par activite
    recente. 3 requetes au total, peu importe le nombre de conversations."""
    conversations = (
        Conversation.objects.select_related("client")
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    unread_rows = (
        Message.objects.filter(sender__is_staff=False)
        .exclude(status=Message.Status.READ)
        .values("conversation_id")
        .annotate(count=Count("id"))
    )
    unread_by_conversation = {row["conversation_id"]: row["count"] for row in unread_rows}

    conversations_data = []
    for conversation in conversations:
        sorted_messages = sorted(
            conversation.messages.all(), key=lambda m: m.created_at, reverse=True
        )
        last_message = sorted_messages[0] if sorted_messages else None

        conversations_data.append(
            {
                "conversation": conversation,
                "last_message": last_message,
                "unread_count": unread_by_conversation.get(conversation.id, 0),
            }
        )

    return render(
        request, "dashboard/conversations_list.html", {"conversations_data": conversations_data}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def change_password(request):
    """Permet a l'administrateur de changer son mot de passe et son nom
    d'utilisateur depuis l'espace de gestion, sans devoir passer par /admin/."""
    if request.method == "POST" and request.POST.get("form_type") == "username":
        username_form = AdminUsernameForm(request.POST, instance=request.user)
        password_form = AdminPasswordChangeForm(user=request.user)
        if username_form.is_valid():
            username_form.save()
            messages.success(request, "Nom d'utilisateur modifie avec succes.")
            return redirect("dashboard:change_password")
    elif request.method == "POST":
        password_form = AdminPasswordChangeForm(user=request.user, data=request.POST)
        username_form = AdminUsernameForm(instance=request.user)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifie avec succes.")
            return redirect("dashboard:change_password")
    else:
        password_form = AdminPasswordChangeForm(user=request.user)
        username_form = AdminUsernameForm(instance=request.user)

    for field in password_form.fields.values():
        field.widget.attrs.update({"class": "field-input"})
    for field in username_form.fields.values():
        field.widget.attrs.update({"class": "field-input"})

    return render(
        request,
        "dashboard/change_password.html",
        {"form": password_form, "username_form": username_form},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversation_detail(request, conversation_id):
    """Vue d'une conversation precise : historique + reponse en temps reel."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    chat_messages = (
        conversation.messages.select_related("sender")
        .prefetch_related("reactions")
        .order_by("created_at")
    )
    return render(
        request,
        "dashboard/conversation.html",
        {"conversation": conversation, "chat_messages": chat_messages},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def company_settings(request):
    """Permet a l'admin de modifier l'identite entreprise et le message
    d'accueil (texte / audio / video, chacun activable independamment)."""
    profile, _ = CompanyProfile.objects.get_or_create(pk=1)
    welcome, _ = WelcomeMessage.objects.get_or_create(pk=1)

    if request.method == "POST" and request.POST.get("form_type") == "profile":
        profile_form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        welcome_form = WelcomeMessageForm(instance=welcome)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profil de l'entreprise mis a jour.")
            return redirect("dashboard:company_settings")
    elif request.method == "POST" and request.POST.get("form_type") == "welcome":
        welcome_form = WelcomeMessageForm(request.POST, request.FILES, instance=welcome)
        profile_form = CompanyProfileForm(instance=profile)
        if welcome_form.is_valid():
            welcome_obj = welcome_form.save(commit=False)
            # Un fichier vient d'etre televerse -> on l'active automatiquement,
            # pour eviter qu'il reste invisible faute d'avoir coche la case.
            if request.FILES.get("audio_file"):
                welcome_obj.is_audio_enabled = True
            if request.FILES.get("video_file"):
                welcome_obj.is_video_enabled = True
            welcome_obj.save()
            messages.success(request, "Message d'accueil mis a jour.")
            return redirect("dashboard:company_settings")
    else:
        profile_form = CompanyProfileForm(instance=profile)
        welcome_form = WelcomeMessageForm(instance=welcome)

    return render(
        request,
        "dashboard/company_settings.html",
        {"profile_form": profile_form, "welcome_form": welcome_form, "profile": profile},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def links_list(request):
    """CRUD des liens externes (WhatsApp, Telegram, etc.) affiches sur la
    page d'accueil publique."""
    links = ExternalLink.objects.all().order_by("order", "id")
    return render(request, "dashboard/links_list.html", {"links": links})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_create(request):
    if request.method == "POST":
        form = ExternalLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lien ajoute.")
            return redirect("dashboard:links_list")
    else:
        form = ExternalLinkForm()
    return render(request, "dashboard/link_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_edit(request, link_id):
    link = get_object_or_404(ExternalLink, id=link_id)
    if request.method == "POST":
        form = ExternalLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, "Lien mis a jour.")
            return redirect("dashboard:links_list")
    else:
        form = ExternalLinkForm(instance=link)
    return render(
        request, "dashboard/link_form.html", {"form": form, "is_edit": True, "link": link}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_delete(request, link_id):
    link = get_object_or_404(ExternalLink, id=link_id)
    if request.method == "POST":
        link.delete()
        messages.success(request, "Lien supprime.")
    return redirect("dashboard:links_list")


# --- Equipes ---------------------------------------------------------------


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def teams_list(request):
    """CRUD des equipes reutilisables entre plusieurs evenements."""
    teams = Team.objects.all()
    return render(request, "dashboard/teams_list.html", {"teams": teams})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipe ajoutee.")
            return redirect("dashboard:teams_list")
    else:
        form = TeamForm()
    return render(request, "dashboard/team_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def team_edit(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipe mise a jour.")
            return redirect("dashboard:teams_list")
    else:
        form = TeamForm(instance=team)
    return render(
        request, "dashboard/team_form.html", {"form": form, "is_edit": True, "team": team}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method == "POST":
        team.delete()
        messages.success(request, "Equipe supprimee.")
    return redirect("dashboard:teams_list")


# --- Evenements --------------------------------------------------------------


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def events_list(request):
    """Liste des evenements sportifs, les plus recents en premier."""
    events = Event.objects.select_related("home_team", "away_team").all()
    return render(request, "dashboard/events_list.html", {"events": events})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Evenement ajoute.")
            return redirect("dashboard:events_list")
    else:
        form = EventForm()
    return render(request, "dashboard/event_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Evenement mis a jour.")
            return redirect("dashboard:events_list")
    else:
        form = EventForm(instance=event)
    return render(
        request, "dashboard/event_form.html", {"form": form, "is_edit": True, "event": event}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Evenement supprime.")
    return redirect("dashboard:events_list")


# --- Pronostics --------------------------------------------------------------


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def predictions_list(request):
    """Liste des pronostics, les plus recents en premier."""
    predictions = Prediction.objects.select_related(
        "event", "event__home_team", "event__away_team", "external_link"
    ).all()
    return render(request, "dashboard/predictions_list.html", {"predictions": predictions})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_create(request):
    if request.method == "POST":
        form = PredictionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pronostic ajoute.")
            return redirect("dashboard:predictions_list")
    else:
        form = PredictionForm()
    return render(request, "dashboard/prediction_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_edit(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    if request.method == "POST":
        form = PredictionForm(request.POST, instance=prediction)
        if form.is_valid():
            form.save()
            messages.success(request, "Pronostic mis a jour.")
            return redirect("dashboard:predictions_list")
    else:
        form = PredictionForm(instance=prediction)
    return render(
        request,
        "dashboard/prediction_form.html",
        {"form": form, "is_edit": True, "prediction": prediction},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_delete(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    if request.method == "POST":
        prediction.delete()
        messages.success(request, "Pronostic supprime.")
    return redirect("dashboard:predictions_list")


# --- Import API-Football ------------------------------------------------


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def fixtures_search(request):
    """Recherche des matchs via l'API-Football pour une date/competition
    donnee, afin de les importer en un clic plutot que de les saisir
    a la main."""
    today = timezone.localdate().isoformat()
    date_str = request.GET.get("date", today)
    league_id = request.GET.get("league") or None

    fixtures = []
    error = None
    already_imported_ids = set()

    if request.GET:
        try:
            fixtures = api_football.search_fixtures(date_str, league_id=league_id)
            already_imported_ids = set(
                Event.objects.filter(
                    api_football_id__in=[f["api_id"] for f in fixtures]
                ).values_list("api_football_id", flat=True)
            )
        except api_football.ApiFootballError as exc:
            error = str(exc)

    return render(
        request,
        "dashboard/fixtures_search.html",
        {
            "fixtures": fixtures,
            "error": error,
            "date_str": date_str,
            "league_id": str(league_id) if league_id else "",
            "already_imported_ids": already_imported_ids,
            "popular_leagues": api_football.POPULAR_LEAGUES,
            "searched": bool(request.GET),
        },
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def fixture_import(request, api_fixture_id):
    """Importe un match choisi dans les resultats de recherche : cree
    (ou reutilise) les deux equipes puis l'evenement, sans jamais
    dupliquer si l'admin importe deux fois le meme match."""
    if request.method != "POST":
        return redirect("dashboard:fixtures_search")

    existing_event = Event.objects.filter(api_football_id=api_fixture_id).first()
    if existing_event:
        messages.info(request, "Ce match a deja ete importe.")
        return redirect("dashboard:event_edit", event_id=existing_event.id)

    date_str = request.POST.get("date_str", timezone.localdate().isoformat())
    league_id = request.POST.get("league_id") or None

    try:
        fixtures = api_football.search_fixtures(date_str, league_id=league_id)
    except api_football.ApiFootballError as exc:
        messages.error(request, f"Import impossible : {exc}")
        return redirect("dashboard:fixtures_search")

    fixture = next((f for f in fixtures if str(f["api_id"]) == str(api_fixture_id)), None)
    if not fixture:
        messages.error(request, "Ce match n'est plus disponible dans les resultats.")
        return redirect("dashboard:fixtures_search")

    home_team, _ = Team.objects.get_or_create(
        api_football_id=fixture["home_id"],
        defaults={"name": fixture["home_name"], "logo_url": fixture["home_logo"]},
    )
    away_team, _ = Team.objects.get_or_create(
        api_football_id=fixture["away_id"],
        defaults={"name": fixture["away_name"], "logo_url": fixture["away_logo"]},
    )

    Event.objects.create(
        home_team=home_team,
        away_team=away_team,
        competition=fixture["competition"],
        sport="Football",
        kickoff_at=fixture["kickoff_at"],
        api_football_id=fixture["api_id"],
    )
    messages.success(request, "Match importe. Ajoute maintenant ton pronostic.")
    return redirect("dashboard:prediction_create")
SPORTI_EOF
echo "  ecrit: apps/dashboard/views.py"

mkdir -p "$(dirname "apps/dashboard/urls.py")"
cat > apps/dashboard/urls.py << 'SPORTI_EOF'
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "dashboard"

urlpatterns = [
    path("connexion/", views.DashboardLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(next_page="/gestion/connexion/"), name="logout"),
    # Comme WhatsApp : l'ouverture de l'espace de gestion mene directement
    # aux conversations, pas aux statistiques.
    path(
        "",
        RedirectView.as_view(pattern_name="dashboard:conversations_list", permanent=False),
        name="home",
    ),
    path("statistiques/", views.dashboard_home, name="stats"),
    path("mot-de-passe/", views.change_password, name="change_password"),
    path("conversations/", views.conversations_list, name="conversations_list"),
    path(
        "conversations/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    path("entreprise/", views.company_settings, name="company_settings"),
    path("liens/", views.links_list, name="links_list"),
    path("liens/nouveau/", views.link_create, name="link_create"),
    path("liens/<int:link_id>/modifier/", views.link_edit, name="link_edit"),
    path("liens/<int:link_id>/supprimer/", views.link_delete, name="link_delete"),
    path("equipes/", views.teams_list, name="teams_list"),
    path("equipes/nouveau/", views.team_create, name="team_create"),
    path("equipes/<int:team_id>/modifier/", views.team_edit, name="team_edit"),
    path("equipes/<int:team_id>/supprimer/", views.team_delete, name="team_delete"),
    path("evenements/", views.events_list, name="events_list"),
    path("evenements/nouveau/", views.event_create, name="event_create"),
    path("evenements/<int:event_id>/modifier/", views.event_edit, name="event_edit"),
    path("evenements/<int:event_id>/supprimer/", views.event_delete, name="event_delete"),
    path("pronostics/", views.predictions_list, name="predictions_list"),
    path("pronostics/nouveau/", views.prediction_create, name="prediction_create"),
    path("pronostics/<int:prediction_id>/modifier/", views.prediction_edit, name="prediction_edit"),
    path(
        "pronostics/<int:prediction_id>/supprimer/",
        views.prediction_delete,
        name="prediction_delete",
    ),
    path("importer-matchs/", views.fixtures_search, name="fixtures_search"),
    path(
        "importer-matchs/<int:api_fixture_id>/importer/",
        views.fixture_import,
        name="fixture_import",
    ),
]
SPORTI_EOF
echo "  ecrit: apps/dashboard/urls.py"

mkdir -p "$(dirname "templates/dashboard/_base.html")"
cat > templates/dashboard/_base.html << 'SPORTI_EOF'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block content %}
<div class="dashboard-shell">
    <aside class="dashboard-sidebar">
        <div class="flex items-center gap-2 mb-8 px-1">
            <div class="w-8 h-8 hud-corners flex items-center justify-center bg-navy-950 overflow-hidden">
                <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
            </div>
            <span class="font-display font-bold tracking-wide">SPORTI</span>
        </div>

        <nav class="flex-1">
            <a href="{% url 'dashboard:conversations_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'conversations_list' or request.resolver_match.url_name == 'conversation_detail' %}active{% endif %}">
                {% trans "Conversations" %}
            </a>
            <a href="{% url 'dashboard:stats' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'stats' %}active{% endif %}">
                {% trans "Vue d'ensemble" %}
            </a>
            <a href="{% url 'dashboard:company_settings' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'company_settings' %}active{% endif %}">
                {% trans "Accueil & Profil" %}
            </a>
            <a href="{% url 'dashboard:links_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name in 'links_list link_create link_edit' %}active{% endif %}">
                {% trans "Liens externes" %}
            </a>
            <a href="{% url 'dashboard:fixtures_search' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'fixtures_search' %}active{% endif %}">
                {% trans "Importer des matchs" %}
            </a>
            <a href="{% url 'dashboard:predictions_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name in 'predictions_list prediction_create prediction_edit' %}active{% endif %}">
                {% trans "Pronostics" %}
            </a>
            <a href="{% url 'dashboard:events_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name in 'events_list event_create event_edit' %}active{% endif %}">
                {% trans "Événements" %}
            </a>
            <a href="{% url 'dashboard:teams_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name in 'teams_list team_create team_edit' %}active{% endif %}">
                {% trans "Équipes" %}
            </a>
            <a href="{% url 'dashboard:change_password' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'change_password' %}active{% endif %}">
                {% trans "Mot de passe" %}
            </a>
        </nav>

        <form method="post" action="{% url 'dashboard:logout' %}">
            {% csrf_token %}
            <button type="submit" class="dashboard-nav-link w-full text-left">
                {% trans "Déconnexion" %}
            </button>
        </form>
    </aside>

    <div class="flex-1 min-w-0 flex flex-col">
        <div class="dashboard-topbar">
            <span class="font-display font-bold">SPORTI</span>
            <div class="flex items-center gap-3 text-xs">
                <a href="{% url 'dashboard:conversations_list' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Chat" %}</a>
                <a href="{% url 'dashboard:stats' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Vue" %}</a>
                <a href="{% url 'dashboard:company_settings' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Accueil" %}</a>
                <a href="{% url 'dashboard:links_list' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Liens" %}</a>
                <a href="{% url 'dashboard:predictions_list' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Pronostics" %}</a>
            </div>
        </div>

        <main class="dashboard-main">
            {% if messages %}
                <div class="mb-6 space-y-2">
                    {% for message in messages %}
                        <div class="px-4 py-3 text-sm border border-accent-500/25 bg-accent-500/5 text-accent-700 dark:text-accent-300">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
            {% block dashboard_content %}{% endblock %}
        </main>
    </div>
</div>
{% endblock %}
SPORTI_EOF
echo "  ecrit: templates/dashboard/_base.html"

mkdir -p "$(dirname "templates/dashboard/fixtures_search.html")"
cat > templates/dashboard/fixtures_search.html << 'SPORTI_EOF'
{% extends "dashboard/_base.html" %}
{% load i18n %}
{% block title %}{% trans "Importer des matchs" %} — SPORTI{% endblock %}
{% block dashboard_content %}
<h1 class="dashboard-page-title">{% trans "Importer des matchs (API-Football)" %}</h1>
<p class="dashboard-page-subtitle">
    {% trans "Recherche des matchs reels et importe-les en un clic plutot que de les saisir a la main." %}
</p>

<form method="get" class="panel !p-5 flex flex-wrap items-end gap-4 mb-6">
    <div class="field-group !mb-0">
        <label for="id_date" class="field-label">{% trans "Date" %}</label>
        <input type="date" id="id_date" name="date" value="{{ date_str }}" class="field-input">
    </div>
    <div class="field-group !mb-0">
        <label for="id_league" class="field-label">{% trans "Competition (optionnel)" %}</label>
        <select id="id_league" name="league" class="field-input">
            <option value="">{% trans "Toutes competitions" %}</option>
            {% for league_value, league_label in popular_leagues %}
            <option value="{{ league_value }}" {% if league_id == league_value|stringformat:"s" %}selected{% endif %}>
                {{ league_label }}
            </option>
            {% endfor %}
        </select>
    </div>
    <button type="submit" class="btn-primary !px-6">{% trans "Rechercher" %}</button>
</form>

{% if error %}
<div class="panel !p-5 mb-6 !border-red-500/30">
    <p class="text-sm text-red-500 font-medium">{{ error }}</p>
    {% if "API_FOOTBALL_KEY" in error or "cle" in error %}
    <p class="text-xs text-navy-900/50 dark:text-white/45 mt-2">
        {% trans "Ajoute ta cle dans le fichier .env : API_FOOTBALL_KEY=ta-cle-ici, puis relance le serveur." %}
    </p>
    {% endif %}
</div>
{% endif %}

{% if fixtures %}
<div class="panel !p-0 overflow-x-auto">
    <table class="data-table">
        <thead>
            <tr>
                <th class="px-6">{% trans "Match" %}</th>
                <th>{% trans "Competition" %}</th>
                <th>{% trans "Date" %}</th>
                <th class="pr-6 text-right">{% trans "Action" %}</th>
            </tr>
        </thead>
        <tbody>
            {% for fixture in fixtures %}
            <tr>
                <td class="px-6 font-medium">{{ fixture.home_name }} — {{ fixture.away_name }}</td>
                <td class="text-navy-900/60 dark:text-white/50">{{ fixture.competition }}</td>
                <td class="text-navy-900/45 dark:text-white/40">{{ fixture.kickoff_at }}</td>
                <td class="pr-6 text-right">
                    {% if fixture.api_id in already_imported_ids %}
                        <span class="badge">{% trans "Deja importe" %}</span>
                    {% else %}
                        <form method="post" action="{% url 'dashboard:fixture_import' fixture.api_id %}" class="inline">
                            {% csrf_token %}
                            <input type="hidden" name="date_str" value="{{ date_str }}">
                            <input type="hidden" name="league_id" value="{{ league_id }}">
                            <button type="submit" class="btn-ghost !px-3 !py-1.5 !text-xs">{% trans "Importer" %}</button>
                        </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% elif not error and searched %}
<div class="panel text-center py-10 text-sm text-navy-900/40 dark:text-white/35">
    {% trans "Aucun match trouve pour cette date/competition." %}
</div>
{% endif %}
{% endblock %}
SPORTI_EOF
echo "  ecrit: templates/dashboard/fixtures_search.html"

mkdir -p "$(dirname "templates/predictions/list.html")"
cat > templates/predictions/list.html << 'SPORTI_EOF'
{% extends "base.html" %}
{% load i18n static %}
{% block title %}{% trans "Pronostics" %} — SPORTI{% endblock %}
{% block content %}
<div class="chats-shell">
    {% include "chat/_top_navbar.html" %}
    <header class="mobile-chat-header lg:hidden !pr-24">
        <div>
            <h1 class="font-display text-lg font-bold">{% trans "Pronostics" %}</h1>
            <p class="text-xs text-navy-900/45 dark:text-white/40">{% trans "Analyses professionnelles du jour" %}</p>
        </div>
        <div class="w-10 h-10 hud-corners bg-navy-950 flex items-center justify-center overflow-hidden shrink-0">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
    </header>

    <div class="flex-1 min-h-0 overflow-y-auto px-4 lg:px-8 py-4 lg:py-8">
        <div class="lg:max-w-3xl lg:mx-auto">
        <h1 class="hidden lg:block font-display text-2xl font-bold mb-1">{% trans "Pronostics" %}</h1>
        <p class="hidden lg:block text-sm text-navy-900/50 dark:text-white/45 mb-6">{% trans "Analyses professionnelles du jour" %}</p>
        <!-- Onglets de filtre -->
        <div class="flex gap-2 mb-5 overflow-x-auto pb-1">
            <a href="?filtre=tous" class="shrink-0 px-4 py-2 text-xs font-display font-semibold uppercase tracking-wide transition-colors
                       {% if active_filter == 'tous' %}bg-accent-600 text-white{% else %}bg-navy-900/[0.04] dark:bg-white/5 text-navy-900/60 dark:text-white/50{% endif %}">
                {% trans "Tous" %}
            </a>
            <a href="?filtre=aujourdhui" class="shrink-0 px-4 py-2 text-xs font-display font-semibold uppercase tracking-wide transition-colors
                       {% if active_filter == 'aujourdhui' %}bg-accent-600 text-white{% else %}bg-navy-900/[0.04] dark:bg-white/5 text-navy-900/60 dark:text-white/50{% endif %}">
                {% trans "Aujourd'hui" %}
            </a>
            <a href="?filtre=top" class="shrink-0 px-4 py-2 text-xs font-display font-semibold uppercase tracking-wide transition-colors
                       {% if active_filter == 'top' %}bg-accent-600 text-white{% else %}bg-navy-900/[0.04] dark:bg-white/5 text-navy-900/60 dark:text-white/50{% endif %}">
                &#9733; {% trans "Top matchs" %}
            </a>
        </div>

        <!-- Bandeau statistiques -->
        <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="stat-card !py-3 !px-4">
                <p class="stat-card-label !mb-1">{% trans "Pronostics publiés" %}</p>
                <p class="stat-card-value !text-2xl">{{ total_count }}</p>
            </div>
            <div class="stat-card !py-3 !px-4">
                <p class="stat-card-label !mb-1">{% trans "Gagnés" %}</p>
                <p class="stat-card-value !text-2xl text-emerald-500">{{ won_count }}</p>
            </div>
        </div>

        <!-- Liste des pronostics -->
        <div class="space-y-3">
            {% for prediction in predictions %}
            <div class="panel !p-4 {% if prediction.is_featured %}!border-accent-500/40{% endif %}">
                <div class="flex items-center justify-between mb-3 text-xs text-navy-900/45 dark:text-white/40">
                    <span>{{ prediction.event.kickoff_at|date:"d M Y • H:i" }} &middot; {{ prediction.event.competition }}</span>
                    {% if prediction.is_featured %}<span class="text-accent-600 dark:text-accent-400 font-semibold">&#9733; {% trans "Top" %}</span>{% endif %}
                </div>

                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                        {% if prediction.event.home_team.display_logo_url %}
                            <img src="{{ prediction.event.home_team.display_logo_url }}" alt="" class="w-8 h-8 object-cover rounded-full shrink-0">
                        {% else %}
                            <span class="avatar-circle shrink-0">{{ prediction.event.home_team.initials }}</span>
                        {% endif %}
                        <span class="text-sm font-medium truncate">{{ prediction.event.home_team.name }}</span>
                    </div>
                    <span class="px-3 text-xs font-display text-navy-900/35 dark:text-white/30">{% trans "VS" %}</span>
                    <div class="flex items-center gap-2 flex-1 min-w-0 justify-end">
                        <span class="text-sm font-medium truncate text-right">{{ prediction.event.away_team.name }}</span>
                        {% if prediction.event.away_team.display_logo_url %}
                            <img src="{{ prediction.event.away_team.display_logo_url }}" alt="" class="w-8 h-8 object-cover rounded-full shrink-0">
                        {% else %}
                            <span class="avatar-circle shrink-0">{{ prediction.event.away_team.initials }}</span>
                        {% endif %}
                    </div>
                </div>

                <div class="flex items-center justify-between gap-3 mb-1">
                    <p class="text-sm">
                        <span class="text-navy-900/45 dark:text-white/40">{% trans "Pronostic" %} :</span>
                        <span class="font-semibold text-accent-600 dark:text-accent-400">{{ prediction.pick }}</span>
                    </p>
                    {% if prediction.confidence %}
                    <span class="text-xs font-semibold text-emerald-500 shrink-0">{% trans "Confiance" %} {{ prediction.confidence }}%</span>
                    {% endif %}
                </div>

                {% if prediction.analysis %}
                <p class="text-xs text-navy-900/50 dark:text-white/45 mt-2">{{ prediction.analysis }}</p>
                {% endif %}

                {% if prediction.odds %}
                <p class="text-xs text-navy-900/45 dark:text-white/40 mt-2">{% trans "Cote" %} : <span class="font-medium">{{ prediction.odds }}</span></p>
                {% endif %}

                {% if prediction.external_link %}
                <a href="{{ prediction.external_link.url }}" target="_blank" rel="noopener noreferrer"
                   class="btn-primary w-full mt-3 !text-xs">
                    {% trans "Parier avec" %} {{ prediction.external_link.label|default:prediction.external_link.get_platform_display }}
                    {% if prediction.external_link.promo_code %}<span class="opacity-80">&middot; {{ prediction.external_link.promo_code }}</span>{% endif %}
                </a>
                {% endif %}
            </div>
            {% empty %}
            <div class="panel text-center py-12 text-sm text-navy-900/40 dark:text-white/35">
                {% trans "Aucun pronostic pour le moment. Revenez bientôt !" %}
            </div>
            {% endfor %}
        </div>
        </div>
    </div>

    {% include "chat/_bottom_nav.html" %}
</div>
{% endblock %}
SPORTI_EOF
echo "  ecrit: templates/predictions/list.html"

mkdir -p "$(dirname "templates/dashboard/teams_list.html")"
cat > templates/dashboard/teams_list.html << 'SPORTI_EOF'
{% extends "dashboard/_base.html" %}
{% load i18n %}
{% block title %}{% trans "Équipes" %} — SPORTI{% endblock %}
{% block dashboard_content %}
<div class="flex items-center justify-between mb-1">
    <h1 class="dashboard-page-title mb-0">{% trans "Équipes" %}</h1>
    <a href="{% url 'dashboard:team_create' %}" class="btn-primary text-xs !px-4 !py-2.5">{% trans "+ Ajouter une équipe" %}</a>
</div>
<p class="dashboard-page-subtitle">
    {% trans "Équipes réutilisables pour créer des événements sportifs." %}
</p>
<div class="panel !p-0 overflow-x-auto">
    <table class="data-table">
        <thead>
            <tr>
                <th class="px-6">{% trans "Logo" %}</th>
                <th>{% trans "Nom" %}</th>
                <th class="pr-6 text-right">{% trans "Actions" %}</th>
            </tr>
        </thead>
        <tbody>
            {% for team in teams %}
            <tr>
                <td class="px-6">
                    {% if team.display_logo_url %}
                        <img src="{{ team.display_logo_url }}" alt="{{ team.name }}" class="w-8 h-8 object-cover">
                    {% else %}
                        <span class="w-8 h-8 flex items-center justify-center bg-navy-900/10 dark:bg-white/10 text-xs font-semibold">{{ team.initials }}</span>
                    {% endif %}
                </td>
                <td class="font-medium">{{ team.name }}</td>
                <td class="pr-6 text-right whitespace-nowrap">
                    <a href="{% url 'dashboard:team_edit' team.id %}" class="btn-ghost !px-2 !py-1 !text-xs">{% trans "Modifier" %}</a>
                    <form method="post" action="{% url 'dashboard:team_delete' team.id %}" class="inline"
                          onsubmit="return confirm('{% trans "Supprimer cette équipe ?" %}');">
                        {% csrf_token %}
                        <button type="submit" class="btn-ghost !px-2 !py-1 !text-xs !text-red-500 hover:!text-red-600">{% trans "Supprimer" %}</button>
                    </form>
                </td>
            </tr>
            {% empty %}
            <tr><td colspan="3" class="px-6 py-10 text-center text-navy-900/40 dark:text-white/35">
                {% trans "Aucune équipe pour le moment." %}
            </td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
SPORTI_EOF
echo "  ecrit: templates/dashboard/teams_list.html"

if ! grep -q "API_FOOTBALL_KEY" config/settings/base.py; then
cat >> config/settings/base.py << 'SPORTI_EOF'

# --- API-Football (v3.football.api-sports.io) ---
# Cle recuperee sur https://dashboard.api-football.com (plan gratuit
# disponible). Utilise le header "x-apisports-key" -- si le compte a ete
# cree via RapidAPI plutot que directement sur api-football.com, il
# faudra adapter apps/predictions/api_football.py pour les headers
# x-rapidapi-key / x-rapidapi-host a la place.
API_FOOTBALL_KEY = env("API_FOOTBALL_KEY", default="")
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
SPORTI_EOF
echo "  ajoute: config/settings/base.py"
else
echo "  deja present: config/settings/base.py (ignore)"
fi

if ! grep -q "API_FOOTBALL_KEY" .env.example; then
cat >> .env.example << 'SPORTI_EOF'

# --- API-Football (import automatique des matchs) ---
# Cle du plan gratuit sur https://dashboard.api-football.com
API_FOOTBALL_KEY=
SPORTI_EOF
echo "  ajoute: .env.example"
else
echo "  deja present: .env.example (ignore)"
fi

echo ""
echo "Termine. Prochaines etapes :"
echo "  1. DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py makemigrations --check"
echo "  2. DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py migrate"
echo "  3. Ajoute API_FOOTBALL_KEY=ta-cle dans ton fichier .env"
echo "  4. python manage.py runserver"
