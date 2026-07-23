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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AppSettings  # Ajuste selon le nom de ton app

# ================= VUE GESTIONNAIRE (ADMIN) =================
@login_required
def admin_dashboard(request):
    # Vérification si c'est un administrateur/staff
    if not request.user.is_staff:
        return redirect('client_home')

    settings = AppSettings.get_settings()

    if request.method == 'POST':
        settings.welcome_message = request.POST.get('welcome_message', '')
        settings.telegram_url = request.POST.get('telegram_url', '')
        settings.whatsapp_url = request.POST.get('whatsapp_url', '')
        settings.save()
        return redirect('admin_dashboard')

    context = {
        'welcome_message': settings.welcome_message,
        'telegram_url': settings.telegram_url,
        'whatsapp_url': settings.whatsapp_url,
        'total_clients': 10, # Remplace par tes requêtes de données si existantes
        'total_conversations': 5,
    }
    return render(request, 'dashboard/home.html', context)


# ================= VUE CLIENT =================
@login_required
def client_dashboard(request):
    settings = AppSettings.get_settings()

    context = {
        'welcome_message': settings.welcome_message,
        'telegram_url': settings.telegram_url,
        'whatsapp_url': settings.whatsapp_url,
    }
    return render(request, 'account/home.html', context)