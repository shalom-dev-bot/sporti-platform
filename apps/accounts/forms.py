"""
Formulaires personnalises pour l'authentification.

SportiSignupForm ajoute un champ "nom" obligatoire et unique a
l'inscription (en plus de l'email pour la connexion). Le message
d'erreur de doublon est explicite et en francais, plutot que de
dependre de la chaine par defaut d'allauth.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from allauth.account.forms import LoginForm, SignupForm

from .models import User


class SportiLoginForm(LoginForm):
    """Ajoute les classes CSS du design system aux champs de connexion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "accent-accent-600"})
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs.update({"class": f"{existing} field-input".strip()})
        if "login" in self.fields:
            self.fields["login"].widget.attrs.update({"placeholder": "vous@exemple.com"})
        if "password" in self.fields:
            self.fields["password"].widget.attrs.update(
                {"placeholder": "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"}
            )


class SportiSignupForm(SignupForm):
    """Ajoute et personnalise le champ nom d'utilisateur a l'inscription."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs.update({"class": f"{existing} field-input".strip()})

        if "username" in self.fields:
            self.fields["username"].label = _("Nom")
            self.fields["username"].widget.attrs.update(
                {
                    "placeholder": _("Votre nom ou pseudo"),
                    "autocomplete": "username",
                }
            )
            self.fields["username"].error_messages["unique"] = _(
                "Ce nom existe deja, choisissez-en un autre."
            )

        if "email" in self.fields:
            self.fields["email"].widget.attrs.update({"placeholder": "vous@exemple.com"})
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({"placeholder": "••••••••••"})
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({"placeholder": "••••••••••"})

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_("Ce nom existe deja, choisissez-en un autre."))
        return username


class ProfileForm(forms.ModelForm):
    """Permet a un client de modifier ses propres informations -- jamais
    celles d'un autre utilisateur."""

    class Meta:
        model = User
        fields = ["avatar", "username", "first_name", "last_name", "phone_number"]
        labels = {
            "avatar": _("Photo de profil"),
            "username": _("Nom"),
            "first_name": _("Prenom"),
            "last_name": _("Nom de famille"),
            "phone_number": _("Telephone"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        file_css = (
            "field-input file:mr-3 file:py-1.5 file:px-3 file:border-0 "
            "file:bg-accent-600 file:text-white file:text-xs file:uppercase file:tracking-wide"
        )
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": file_css if name == "avatar" else "field-input"})

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if (
            username
            and User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists()
        ):
            raise forms.ValidationError(_("Ce nom existe deja, choisissez-en un autre."))
        return username
