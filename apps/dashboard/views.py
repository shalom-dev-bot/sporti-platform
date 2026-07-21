"""
Espace de gestion de l'entreprise -- interface personnalisee SPORTI,
distincte de l'admin Django par defaut (reserve aux developpeurs sur /admin/).
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator

from django_ratelimit.decorators import ratelimit

from apps.accounts.models import User
from apps.chat.models import Conversation, Message


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class DashboardLoginView(LoginView):
    """Connexion admin limitee a 5 tentatives par minute et par IP,
    pour se proteger contre les attaques par force brute sur le mot
    de passe."""

    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/gestion/"


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def dashboard_home(request):
    """Vue d'ensemble : statistiques cles et evolution du nombre de clients."""
    total_clients = User.objects.filter(is_staff=False).count()
    total_conversations = Conversation.objects.count()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = Message.objects.filter(created_at__gte=today_start).count()

    unread_conversations = (
        Conversation.objects.exclude(messages__status=Message.Status.READ)
        .filter(messages__sender__is_staff=False)
        .distinct()
        .count()
    )

    # Evolution du nombre de clients inscrits, mois par mois (12 derniers mois).
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
    return render(request, "dashboard/home.html", context)


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversations_list(request):
    """Liste complete et organisee de tous les clients qui discutent
    avec l'entreprise, triee par activite la plus recente."""
    conversations = (
        Conversation.objects.select_related("client")
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    conversations_data = []
    for conversation in conversations:
        last_message = conversation.messages.order_by("-created_at").first()
        unread_count = (
            conversation.messages.filter(sender__is_staff=False)
            .exclude(status=Message.Status.READ)
            .count()
        )
        conversations_data.append(
            {
                "conversation": conversation,
                "last_message": last_message,
                "unread_count": unread_count,
            }
        )

    return render(
        request, "dashboard/conversations_list.html", {"conversations_data": conversations_data}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversation_detail(request, conversation_id):
    """Vue d'une conversation precise : historique + reponse en temps reel
    (la connexion WebSocket se fait cote client, en JavaScript, vers
    ws/chat/<conversation_id>/)."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.select_related("sender").order_by("created_at")
    return render(
        request,
        "dashboard/conversation.html",
        {"conversation": conversation, "messages": messages},
    )
