"""
Formulaires specifiques a l'espace de gestion admin : mot de passe avec
regle simplifiee (6 caracteres minimum, sans exigences supplementaires)
et modification du nom d'utilisateur.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from apps.company.models import ExternalLink
from apps.predictions.models import Event, Prediction, Team

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


class _StyledPredictionFormMixin:
    def _apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "accent-accent-600 w-4 h-4"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {
                        "class": "field-input file:mr-3 file:py-1.5 file:px-3 file:border-0 file:bg-accent-600 file:text-white file:text-xs file:uppercase file:tracking-wide"
                    }
                )
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update(
                    {"class": "field-input", "rows": field.widget.attrs.get("rows", 3)}
                )
            else:
                field.widget.attrs.update({"class": "field-input"})


class TeamForm(_StyledPredictionFormMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "logo"]
        labels = {"name": "Nom de l'equipe", "logo": "Logo (optionnel)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class EventForm(_StyledPredictionFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ["home_team", "away_team", "competition", "sport", "kickoff_at"]
        labels = {
            "home_team": "Equipe a domicile",
            "away_team": "Equipe a l'exterieur",
            "competition": "Competition",
            "sport": "Sport",
            "kickoff_at": "Date et heure du match",
        }
        widgets = {
            "kickoff_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()
        self.fields["kickoff_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class PredictionForm(_StyledPredictionFormMixin, forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ["event", "pick", "analysis", "odds", "external_link", "result", "is_published"]
        labels = {
            "event": "Evenement",
            "pick": "Pronostic",
            "analysis": "Analyse detaillee (optionnel)",
            "odds": "Cote (optionnel)",
            "external_link": "Plateforme de paris recommandee (optionnel)",
            "result": "Resultat",
            "is_published": "Visible par les clients",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["external_link"].queryset = ExternalLink.objects.filter(category="platform")
        self._apply_styles()
