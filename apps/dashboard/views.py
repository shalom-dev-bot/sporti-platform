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
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.company.forms import (
    CompanyProfileForm,
    ExternalLinkForm,
    WelcomeAudioForm,
    WelcomeTextForm,
)
from apps.company.models import CompanyProfile, ExternalLink, WelcomeMessage
from apps.predictions import api_football, football_data
from apps.predictions.models import Event, Prediction, Team
from apps.predictions.views import LIVE_MATCH_WINDOW

from .forms import (
    AdminPasswordChangeForm,
    AdminProfileForm,
    AdminUsernameForm,
    EventForm,
    PredictionCoreForm,
    PredictionForm,
    TeamForm,
)

CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"
CACHE_TTL_DASHBOARD_STATS = 60  # secondes : assez court pour rester a jour,
# assez long pour eviter de recalculer a chaque chargement de page.


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/gestion/statistiques/"


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def dashboard_home(request):
    """Vue d'ensemble : statistiques cles, acces rapide et activite recente.
    Mise en cache Redis : les statistiques ne sont recalculees qu'une fois
    par minute maximum, meme si plusieurs admins consultent la page en
    meme temps. Cle en cache par langue active : l'activite recente contient
    du texte traduit, un admin FR ne doit jamais recevoir le cache d'un
    admin EN (et inversement)."""
    cache_key = f"{CACHE_KEY_DASHBOARD_STATS}:{get_language()}"
    context = cache.get(cache_key)
    if context is None:
        from apps.dashboard.models import SiteVisit

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        total_clients = User.objects.filter(is_staff=False).count()
        active_clients = User.objects.filter(is_staff=False, is_active=True).count()
        new_clients_today = User.objects.filter(
            is_staff=False, date_joined__gte=today_start
        ).count()

        total_conversations = Conversation.objects.count()
        new_conversations_today = Conversation.objects.filter(created_at__gte=today_start).count()

        published_predictions = Prediction.objects.filter(is_published=True)
        total_predictions = published_predictions.count()
        won_predictions = published_predictions.filter(result=Prediction.Result.WON).count()
        success_rate = (
            round((won_predictions / total_predictions) * 100) if total_predictions else 0
        )
        active_predictions = published_predictions.filter(result=Prediction.Result.PENDING).count()
        new_predictions_today = Prediction.objects.filter(created_at__gte=today_start).count()

        messages_today = Message.objects.filter(created_at__gte=today_start).count()

        unread_conversations = (
            Conversation.objects.filter(messages__sender__is_staff=False)
            .exclude(messages__status=Message.Status.READ)
            .distinct()
            .count()
        )

        visits_today = (
            SiteVisit.objects.filter(date=today).values_list("count", flat=True).first() or 0
        )
        visits_yesterday = (
            SiteVisit.objects.filter(date=yesterday).values_list("count", flat=True).first() or 0
        )
        if visits_yesterday:
            visits_change_percent = round(
                (visits_today - visits_yesterday) / visits_yesterday * 100, 1
            )
        else:
            visits_change_percent = None

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

        activity = []
        for u in User.objects.filter(is_staff=False).order_by("-date_joined")[:5]:
            activity.append(
                {
                    "kind": "member",
                    "title": _("Nouveau membre"),
                    "detail": _("%(user)s a rejoint SPORTI") % {"user": u},
                    "at": u.date_joined,
                }
            )
        for p in (
            Prediction.objects.filter(is_published=True)
            .select_related("event__home_team", "event__away_team")
            .order_by("-created_at")[:5]
        ):
            activity.append(
                {
                    "kind": "prediction",
                    "title": _("Pronostic publié"),
                    "detail": f"{p.event.home_team} vs {p.event.away_team}",
                    "at": p.created_at,
                }
            )
        for m in (
            Message.objects.filter(sender__is_staff=False)
            .select_related("sender")
            .order_by("-created_at")[:5]
        ):
            activity.append(
                {
                    "kind": "message",
                    "title": _("Nouveau message"),
                    "detail": _("De : %(sender)s") % {"sender": m.sender},
                    "at": m.created_at,
                }
            )
        activity.sort(key=lambda item: item["at"], reverse=True)
        activity = activity[:6]

        context = {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "new_clients_today": new_clients_today,
            "total_conversations": total_conversations,
            "new_conversations_today": new_conversations_today,
            "messages_today": messages_today,
            "unread_conversations": unread_conversations,
            "success_rate": success_rate,
            "active_predictions": active_predictions,
            "new_predictions_today": new_predictions_today,
            "visits_today": visits_today,
            "visits_change_percent": visits_change_percent,
            "growth_labels": growth_labels,
            "growth_values": growth_values,
            "activity": activity,
        }
        cache.set(cache_key, context, CACHE_TTL_DASHBOARD_STATS)

    return render(request, "dashboard/home.html", context)


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def settings_hub(request):
    """Page d'accueil de l'onglet Parametres (mobile) : regroupe tout ce
    qui n'a pas sa propre place dans la barre de navigation principale."""
    return render(request, "dashboard/settings_hub.html")


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def users_list(request):
    """Liste des clients (jamais des membres du staff), avec activation/
    desactivation rapide -- pas d'edition de profil depuis l'admin, un
    client reste seul maitre de ses propres infos."""
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(is_staff=False).order_by("-date_joined")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
        )
    return render(request, "dashboard/users_list.html", {"users": users, "query": query})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def user_toggle_active(request, user_id):
    if request.method != "POST":
        return redirect("dashboard:users_list")
    target = get_object_or_404(User, id=user_id, is_staff=False)
    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    messages.success(request, f"{target} {'reactive' if target.is_active else 'desactive'}.")
    return redirect("dashboard:users_list")


def _conversations_sidebar_data():
    """Donnees de la liste des conversations, triee par activite recente --
    partagees entre la liste et le detail pour que la barre laterale
    (cote desktop, comme WhatsApp Web) soit identique sur les deux pages."""
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
    return conversations_data


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversations_list(request):
    """Liste complete et organisee des conversations. 3 requetes au total,
    peu importe le nombre de conversations."""
    return render(
        request,
        "dashboard/conversations_list.html",
        {"conversations_data": _conversations_sidebar_data()},
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
            messages.success(request, _("Nom d'utilisateur modifie avec succes."))
            return redirect("dashboard:change_password")
    elif request.method == "POST":
        password_form = AdminPasswordChangeForm(user=request.user, data=request.POST)
        username_form = AdminUsernameForm(instance=request.user)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _("Mot de passe modifie avec succes."))
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
    """Vue d'une conversation precise : historique + reponse en temps reel.
    Inclut aussi la liste des conversations pour la barre laterale desktop
    (comme WhatsApp Web : liste a gauche, fil de discussion a droite)."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    chat_messages = (
        conversation.messages.select_related("sender", "reply_to", "reply_to__sender")
        .prefetch_related("reactions", "reply_to__attachments")
        .order_by("created_at")
    )
    welcome, _welcome_created = WelcomeMessage.objects.get_or_create(pk=1)
    return render(
        request,
        "dashboard/conversation.html",
        {
            "conversation": conversation,
            "chat_messages": chat_messages,
            "conversations_data": _conversations_sidebar_data(),
            "active_conversation_id": conversation.id,
            "welcome": welcome,
            "welcome_text": welcome.get_text(get_language()),
        },
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def company_settings(request):
    """Permet a l'admin de modifier son profil personnel, l'identite
    entreprise et le message d'accueil (texte / audio), chacun
    independamment."""
    profile, _profile_created = CompanyProfile.objects.get_or_create(pk=1)
    welcome, _welcome_created = WelcomeMessage.objects.get_or_create(pk=1)
    form_type = request.POST.get("form_type") if request.method == "POST" else None

    admin_profile_form = AdminProfileForm(
        request.POST if form_type == "admin_profile" else None,
        request.FILES if form_type == "admin_profile" else None,
        instance=request.user,
    )
    profile_form = CompanyProfileForm(
        request.POST if form_type == "profile" else None,
        request.FILES if form_type == "profile" else None,
        instance=profile,
    )
    welcome_text_form = WelcomeTextForm(
        request.POST if form_type == "welcome_text" else None,
        instance=welcome,
    )
    welcome_audio_form = WelcomeAudioForm(
        request.POST if form_type == "welcome_audio" else None,
        request.FILES if form_type == "welcome_audio" else None,
        instance=welcome,
    )

    if form_type == "admin_profile" and admin_profile_form.is_valid():
        admin_profile_form.save()
        messages.success(request, _("Profil administrateur mis a jour."))
        return redirect("dashboard:company_settings")
    if form_type == "profile" and profile_form.is_valid():
        profile_form.save()
        messages.success(request, _("Profil de l'entreprise mis a jour."))
        return redirect("dashboard:company_settings")
    if form_type == "welcome_text" and welcome_text_form.is_valid():
        welcome_text_form.save()
        messages.success(request, _("Message d'accueil mis a jour."))
        return redirect("dashboard:company_settings")
    if form_type == "welcome_audio" and welcome_audio_form.is_valid():
        welcome_obj = welcome_audio_form.save(commit=False)
        # Un fichier vient d'etre televerse -> on l'active automatiquement,
        # pour eviter qu'il reste invisible faute d'avoir coche la case.
        if request.FILES.get("audio_file"):
            welcome_obj.is_audio_enabled = True
        welcome_obj.save()
        messages.success(request, _("Message d'accueil mis a jour."))
        return redirect("dashboard:company_settings")

    return render(
        request,
        "dashboard/company_settings.html",
        {
            "admin_profile_form": admin_profile_form,
            "profile_form": profile_form,
            "welcome_text_form": welcome_text_form,
            "welcome_audio_form": welcome_audio_form,
            "profile": profile,
        },
    )


# Meme palette que platformColor() cote client (templates/chat/room.html) --
# les plateformes de paris (1xbet, melbet...) ne sont pas un choix fixe du
# modele (juste "autre" + un label libre), donc la couleur se determine sur
# le texte du label, pas sur un champ dedie.
_PLATFORM_BRAND_COLORS = {
    "1xbet": "#1f4fff",
    "linebet": "#1f7a3e",
    "winwin": "#5b21b6",
    "melbet": "#0f766e",
    "1win": "#b45309",
    "megaparis": "#475569",
}
_SOCIAL_BRAND_COLORS = {
    "whatsapp": "#25D366",
    "telegram": "#29A9EA",
    "facebook": "#1877F2",
    "instagram": "#C13584",
}


def _link_badge_color(link):
    if link.category == "platform":
        key = (link.label or "").lower().replace(" ", "")
        return _PLATFORM_BRAND_COLORS.get(key, "#5b8def")
    return _SOCIAL_BRAND_COLORS.get(link.platform, "#94a3b8")


def _platform_links_for_picker():
    """Plateformes deja enregistrees, pretes pour le selecteur en pastilles
    du formulaire de pronostic (choisir une plateforme existante vs en
    saisir une nouvelle)."""
    links = list(ExternalLink.objects.filter(category="platform").order_by("order", "id"))
    for link in links:
        link.badge_color = _link_badge_color(link)
        link.display_name = link.label or link.get_platform_display()
    return links


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def links_list(request):
    """CRUD des liens externes (WhatsApp, Telegram, etc.) affiches sur la
    page d'accueil publique."""
    links = list(ExternalLink.objects.all().order_by("order", "id"))
    for link in links:
        link.badge_color = _link_badge_color(link)
    return render(request, "dashboard/links_list.html", {"links": links})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_create(request):
    if request.method == "POST":
        form = ExternalLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Lien ajoute."))
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
            messages.success(request, _("Lien mis a jour."))
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
        messages.success(request, _("Lien supprime."))
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
            messages.success(request, _("Equipe ajoutee."))
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
            messages.success(request, _("Equipe mise a jour."))
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
        messages.success(request, _("Equipe supprimee."))
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
            messages.success(request, _("Evenement ajoute."))
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
            messages.success(request, _("Evenement mis a jour."))
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
        messages.success(request, _("Evenement supprime."))
    return redirect("dashboard:events_list")


# --- Pronostics --------------------------------------------------------------


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def predictions_list(request):
    """Liste des pronostics, avec recherche et filtres par statut -- la
    meme vue que celle publiee cote client, avec la gestion en plus."""
    predictions_qs = Prediction.objects.select_related(
        "event", "event__home_team", "event__away_team", "external_link"
    )

    query = request.GET.get("q", "").strip()
    if query:
        predictions_qs = predictions_qs.filter(
            Q(event__home_team__name__icontains=query)
            | Q(event__away_team__name__icontains=query)
            | Q(pick__icontains=query)
            | Q(event__competition__icontains=query)
        )

    # Le statut (a venir / live / termine) suit uniquement l'heure du match --
    # ce n'est pas a l'admin de le marquer "termine" a la main : des que
    # la fenetre live est depassee, c'est termine, meme si le resultat
    # (gagne/perdu) n'a pas encore ete renseigne.
    now = timezone.now()
    live_start = now - LIVE_MATCH_WINDOW
    counts = {
        "tous": predictions_qs.count(),
        "actifs": predictions_qs.filter(event__kickoff_at__gt=now).count(),
        "en_attente": predictions_qs.filter(
            event__kickoff_at__lte=now, event__kickoff_at__gte=live_start
        ).count(),
        "termines": predictions_qs.filter(event__kickoff_at__lt=live_start).count(),
    }

    active_filter = request.GET.get("filtre", "tous")
    if active_filter == "actifs":
        predictions_qs = predictions_qs.filter(event__kickoff_at__gt=now)
    elif active_filter == "en_attente":
        predictions_qs = predictions_qs.filter(
            event__kickoff_at__lte=now, event__kickoff_at__gte=live_start
        )
    elif active_filter == "termines":
        predictions_qs = predictions_qs.filter(event__kickoff_at__lt=live_start)

    predictions = list(predictions_qs)
    for prediction in predictions:
        kickoff = prediction.event.kickoff_at
        if kickoff > now:
            prediction.status_label = "upcoming"
        elif kickoff >= live_start:
            prediction.status_label = "live"
        else:
            prediction.status_label = "finished"

    return render(
        request,
        "dashboard/predictions_list.html",
        {
            "predictions": predictions,
            "counts": counts,
            "active_filter": active_filter,
            "query": query,
        },
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_create(request):
    """Ecran unifie : cree l'evenement (equipes, competition, date) et le
    pronostic en une seule fois. Si un evenement existe deja (ex: import
    API-Football via fixtures_search), on saute l'etape "evenement" et on
    ne demande que les champs du pronostic."""
    event_id = request.GET.get("event") or request.POST.get("event_id")
    existing_event = get_object_or_404(Event, id=event_id) if event_id else None

    event_form = None
    if request.method == "POST":
        prediction_form = PredictionCoreForm(request.POST)
        event_valid = True
        if not existing_event:
            event_form = EventForm(request.POST)
            event_valid = event_form.is_valid()
        if event_valid and prediction_form.is_valid():
            event = existing_event or event_form.save()
            prediction = prediction_form.save(commit=False)
            prediction.event = event
            prediction.result = Prediction.Result.PENDING
            prediction.save()
            messages.success(request, _("Pronostic ajoute."))
            return redirect("dashboard:predictions_list")
    else:
        prediction_form = PredictionCoreForm()
        if not existing_event:
            event_form = EventForm()

    all_events = []
    if not existing_event:
        events_qs = Event.objects.select_related("home_team", "away_team").order_by("-kickoff_at")[
            :300
        ]
        all_events = [
            {
                "id": e.id,
                "home": e.home_team.name,
                "away": e.away_team.name,
                "home_id": e.home_team_id,
                "away_id": e.away_team_id,
                "competition": e.competition,
                "kickoff": localtime(e.kickoff_at).strftime("%d/%m/%Y %H:%M"),
                "kickoff_input": localtime(e.kickoff_at).strftime("%Y-%m-%dT%H:%M"),
            }
            for e in events_qs
        ]

    return render(
        request,
        "dashboard/prediction_create_form.html",
        {
            "event_form": event_form,
            "prediction_form": prediction_form,
            "existing_event": existing_event,
            "all_events": all_events,
            "platform_links": _platform_links_for_picker(),
        },
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_edit(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    if request.method == "POST":
        form = PredictionForm(request.POST, instance=prediction)
        if form.is_valid():
            form.save()
            messages.success(request, _("Pronostic mis a jour."))
            return redirect("dashboard:predictions_list")
    else:
        form = PredictionForm(instance=prediction)
    return render(
        request,
        "dashboard/prediction_form.html",
        {
            "form": form,
            "is_edit": True,
            "prediction": prediction,
            "platform_links": _platform_links_for_picker(),
        },
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def prediction_delete(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    if request.method == "POST":
        prediction.delete()
        messages.success(request, _("Pronostic supprime."))
    return redirect("dashboard:predictions_list")


# --- Import API-Football ------------------------------------------------


def _merged_fixtures(date_str):
    """Fusionne les resultats de football-data.org (fiable mais limite a
    13 grandes competitions sur le plan gratuit) et d'API-Football
    (beaucoup plus large -- petites competitions incluses -- mais un
    plan gratuit plus fragile : deja suspendu une fois cette session, et
    son parametre "season" est bloque des qu'une competition precise est
    demandee, meme pour l'annee en cours).

    Chaque fournisseur est appele independamment : si l'un des deux
    echoue (quota, suspension, panne), on ignore silencieusement son
    erreur et on garde les resultats de l'autre plutot que de faire
    echouer toute la recherche. Erreur seulement si LES DEUX echouent."""
    fixtures = []
    errors = []

    try:
        fd_fixtures, _fd_quota = football_data.search_fixtures(date_str)
        fixtures.extend(fd_fixtures)
    except football_data.ApiFootballError as exc:
        errors.append(str(exc))

    def _dedup_key(f):
        return (f["home_name"].strip().lower(), f["away_name"].strip().lower(), f["kickoff_at"])

    seen = {_dedup_key(f) for f in fixtures}
    try:
        af_fixtures, _af_quota = api_football.search_fixtures(date_str)
        for fixture in af_fixtures:
            key = _dedup_key(fixture)
            if key not in seen:
                seen.add(key)
                fixtures.append(fixture)
    except api_football.ApiFootballError as exc:
        errors.append(str(exc))

    if not fixtures and errors:
        raise api_football.ApiFootballError(" / ".join(errors))

    fixtures.sort(key=lambda f: f["kickoff_at"] or "")
    return fixtures


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def fixtures_search(request):
    """Recherche des matchs pour une date donnee (football-data.org +
    API-Football fusionnes, voir _merged_fixtures), afin de les importer
    en un clic plutot que de les saisir a la main. Resultats groupes par
    competition.

    Toujours une recherche non filtree par competition : le filtre se
    fait cote client (JS) sur ce resultat unique, sans requete API
    supplementaire -- voir le filtre "Compétition" du template."""
    today = timezone.localdate()
    periode = request.GET.get("periode", "aujourdhui")
    if periode == "demain":
        date_str = (today + timedelta(days=1)).isoformat()
    elif periode == "date" and request.GET.get("date"):
        date_str = request.GET.get("date")
    else:
        periode = "aujourdhui"
        date_str = today.isoformat()
    statut = request.GET.get("statut") or ""

    competitions = []
    error = None
    already_imported_ids = set()
    last_updated = None

    if request.GET:
        try:
            fixtures = _merged_fixtures(date_str)
            last_updated = timezone.now()
            if statut == "a_venir":
                fixtures = [f for f in fixtures if f["status_short"] == "NS"]
            elif statut == "termine":
                fixtures = [f for f in fixtures if f["status_short"] in ("FT", "AET", "PEN")]
            elif statut == "en_cours":
                fixtures = [
                    f for f in fixtures if f["status_short"] in ("1H", "2H", "HT", "ET", "P")
                ]

            for fixture in fixtures:
                fixture["kickoff_dt"] = (
                    parse_datetime(fixture["kickoff_at"]) if fixture.get("kickoff_at") else None
                )
            already_imported_ids = set(
                Event.objects.filter(
                    api_football_id__in=[f["api_id"] for f in fixtures]
                ).values_list("api_football_id", flat=True)
            )

            grouped = {}
            for fixture in fixtures:
                grouped.setdefault(fixture["competition"], []).append(fixture)
            competitions = [
                {"name": name, "count": len(items), "fixtures": items}
                for name, items in sorted(grouped.items())
            ]
        except api_football.ApiFootballError as exc:
            error = str(exc)

    return render(
        request,
        "dashboard/fixtures_search.html",
        {
            "competitions": competitions,
            "error": error,
            "date_str": date_str,
            "periode": periode,
            "statut": statut,
            "already_imported_ids": already_imported_ids,
            "searched": bool(request.GET),
            "last_updated": last_updated,
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
        messages.info(request, _("Ce match a deja ete importe."))
        return redirect("dashboard:event_edit", event_id=existing_event.id)

    # Les donnees du match viennent des champs caches du formulaire (deja
    # recuperees par la recherche qui a affiche ce bouton "Importer") --
    # on evite ainsi un deuxieme appel a l'API-Football rien que pour
    # retrouver un match qu'on a deja sous les yeux.
    home_id = request.POST.get("home_id")
    away_id = request.POST.get("away_id")
    if not home_id or not away_id:
        messages.error(request, _("Donnees du match manquantes, relancez la recherche."))
        return redirect("dashboard:fixtures_search")

    home_team, _home_created = Team.objects.get_or_create(
        api_football_id=home_id,
        defaults={
            "name": request.POST.get("home_name", ""),
            "logo_url": request.POST.get("home_logo", ""),
        },
    )
    away_team, _away_created = Team.objects.get_or_create(
        api_football_id=away_id,
        defaults={
            "name": request.POST.get("away_name", ""),
            "logo_url": request.POST.get("away_logo", ""),
        },
    )

    event = Event.objects.create(
        home_team=home_team,
        away_team=away_team,
        competition=request.POST.get("competition", ""),
        sport="Football",
        kickoff_at=request.POST.get("kickoff_at"),
        api_football_id=api_fixture_id,
    )
    messages.success(request, _("Match importe. Ajoute maintenant ton pronostic."))
    return redirect(f"{reverse('dashboard:prediction_create')}?event={event.id}")
