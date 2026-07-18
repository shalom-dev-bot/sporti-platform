from django.shortcuts import render


def home(request):
    """Page d'accueil : presentation entreprise + acces au chat prive."""
    return render(request, "chat/home.html")


def service_worker(request):
    """Sert le service worker a la racine du site (/service-worker.js),
    obligatoire pour que son 'scope' couvre l'integralite du site."""
    from django.conf import settings
    from django.http import HttpResponse

    with open(settings.BASE_DIR / "static" / "service-worker.js", "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="application/javascript")
