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
