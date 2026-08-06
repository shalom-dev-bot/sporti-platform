"""
Page profil du client : consultation et modification de ses propres
informations uniquement. Un client ne peut jamais voir ni modifier le
profil d'un autre utilisateur -- cette vue n'accepte aucun identifiant
en parametre, elle agit toujours sur request.user.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm


@login_required(login_url="/")
def profile(request):
    if request.user.is_staff:
        return redirect("/gestion/")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis a jour.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
