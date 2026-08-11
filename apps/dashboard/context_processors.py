import os

from django.conf import settings
from django.core.cache import cache

from apps.chat.models import Conversation, Message

CACHE_KEY_UNREAD = "dashboard:unread_conversations"
CACHE_TTL_UNREAD = 15  # secondes : evite de recompter a chaque navigation admin.

_CSS_PATH = settings.BASE_DIR / "static" / "css" / "dist" / "sporti.css"


def static_version(request):
    """Ajoute `?v=<mtime>` derriere sporti.css dans base.html -- sans ca,
    le navigateur (surtout mobile) peut garder en cache une vieille
    version du CSS meme apres un nouveau build, et une page redessinee
    semble "ne pas avoir change" ou "toujours cassee" chez le client."""
    try:
        version = str(int(os.path.getmtime(_CSS_PATH)))
    except OSError:
        version = "0"
    return {"STATIC_VERSION": version}


def admin_nav(request):
    """Rend `unread_conversations` disponible sur toutes les pages admin,
    pas seulement la page d'accueil -- sinon le badge de la bottom-nav
    est correct sur une page et vide sur une autre."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}

    unread_conversations = cache.get(CACHE_KEY_UNREAD)
    if unread_conversations is None:
        unread_conversations = (
            Conversation.objects.filter(messages__sender__is_staff=False)
            .exclude(messages__status=Message.Status.READ)
            .distinct()
            .count()
        )
        cache.set(CACHE_KEY_UNREAD, unread_conversations, CACHE_TTL_UNREAD)

    return {"unread_conversations": unread_conversations}
