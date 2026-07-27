"""
Formulaires specifiques a l'espace de gestion admin : mot de passe avec
regle simplifiee (6 caracteres minimum, sans exigences supplementaires)
et modification du nom d'utilisateur.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()


class AdminPasswordChangeForm(PasswordChangeForm):
    """Mot de passe admin : 6 caracteres minimum, aucune autre regle
    (pas de verification de similarite, de mot de passe courant, etc.)."""

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages["password_mismatch"], code="password_mismatch"
            )
        if password2 and len(password2) < 6:
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins 6 caracteres.",
                code="password_too_short",
            )
        return password2


class AdminUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
        labels = {"username": "Nom d'utilisateur"}
