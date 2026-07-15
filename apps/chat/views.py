from django.shortcuts import render


def home(request):
    """Page d'accueil : presentation entreprise + acces au chat prive."""
    return render(request, "chat/home.html")
