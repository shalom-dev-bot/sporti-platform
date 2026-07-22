"""
Espace de gestion de l'entreprise -- interface personnalisee SPORTI,
distincte de l'admin Django par defaut (reserve aux developpeurs sur /admin/).
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.chat.models import Conversation, Message

CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"
CACHE_TTL_DASHBOARD_STATS = 60  # secondes : assez court pour rester a jour,
# assez long pour eviter de recalculer a chaque chargement de page.


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/gestion/"


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
    """Permet a l'administrateur de changer son mot de passe depuis
    l'espace de gestion, sans devoir passer par /admin/."""
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifie avec succes.")
            return redirect("dashboard:change_password")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "dashboard/change_password.html", {"form": form})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversation_detail(request, conversation_id):
    """Vue d'une conversation precise : historique + reponse en temps reel."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.select_related("sender").order_by("created_at")
    return render(
        request,
        "dashboard/conversation.html",
        {"conversation": conversation, "messages": messages},
    )
