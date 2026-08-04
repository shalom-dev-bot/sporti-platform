from django.shortcuts import redirect, render


def home(request):
    """Page d'accueil publique pour un visiteur, ou ecran de choix
    (hub) une fois le client connecte. Un membre du staff qui atterrit
    ici est renvoye vers son espace de gestion plutot que vers le hub."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("/gestion/")
    if request.user.is_authenticated:
        return render(request, "chat/hub.html")
    return render(request, "chat/home.html")


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
