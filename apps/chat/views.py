from django.shortcuts import render


def home(request):
    """Page d'accueil : presentation entreprise + acces au chat prive."""
    return render(request, "chat/home.html")


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
