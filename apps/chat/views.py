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
