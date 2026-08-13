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


def _get_or_create_platform_link(name, url):
    """Cree (ou reutilise, insensible a la casse) une plateforme de paris
    recommandee a la volee depuis le formulaire de pronostic, pour eviter
    a l'admin de devoir passer par la page 'Liens' au prealable."""
    link = ExternalLink.objects.filter(category="platform", label__iexact=name).first()
    if link is not None:
        return link
    return ExternalLink.objects.create(
        category="platform", platform="other", label=name, url=url or ""
    )


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


class AdminProfileForm(forms.ModelForm):
    """Profil personnel de l'administrateur (Parametres generaux) --
    distinct du profil de l'entreprise (nom/logo public)."""

    class Meta:
        model = User
        fields = ["first_name", "email", "avatar"]
        labels = {
            "first_name": "Nom affiche",
            "email": "E-mail",
            "avatar": "Photo de profil",
        }
        # ClearableFileInput affiche "Currently: <fichier> Clear" en texte
        # brut des qu'un avatar existe deja -- notre UI (cercle + label
        # superpose) gere deja le changement de photo, ce texte est indesirable.
        widgets = {"avatar": forms.FileInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "avatar":
                continue
            field.widget.attrs.update({"class": "field-input"})


class _StyledPredictionFormMixin:
    def _apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "accent-accent-600 w-4 h-4"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {
                        "class": (
                            "field-input file:mr-3 file:py-1.5 file:px-3 "
                            "file:border-0 file:bg-accent-600 file:text-white "
                            "file:text-xs file:uppercase file:tracking-wide"
                        )
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
    custom_platform_name = forms.CharField(
        max_length=100,
        required=False,
        label="Ou saisir le nom d'une nouvelle plateforme",
        help_text=(
            "Cree (ou reutilise) une plateforme recommandee a la volee, " "sans quitter cet ecran."
        ),
    )

    class Meta:
        model = Prediction
        fields = [
            "event",
            "pick",
            "analysis",
            "odds",
            "coupon_code",
            "confidence",
            "is_featured",
            "external_link",
            "custom_bet_url",
            "result",
            "is_published",
        ]
        labels = {
            "event": "Evenement",
            "pick": "Pronostic",
            "analysis": "Analyse detaillee (optionnel)",
            "odds": "Cote (optionnel)",
            "coupon_code": "Code du coupon (optionnel)",
            "confidence": "Confiance % (optionnel)",
            "is_featured": "Match phare (Top matchs)",
            "external_link": "Plateforme de paris recommandee (optionnel)",
            "custom_bet_url": "Ou lien personnalise (optionnel)",
            "result": "Resultat",
            "is_published": "Visible par les clients",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["external_link"].queryset = ExternalLink.objects.filter(category="platform")
        self.fields["external_link"].required = False
        self._apply_styles()

    def save(self, commit=True):
        instance = super().save(commit=False)
        platform_name = self.cleaned_data.get("custom_platform_name", "").strip()
        if platform_name and not instance.external_link_id:
            instance.external_link = _get_or_create_platform_link(
                platform_name, self.cleaned_data.get("custom_bet_url")
            )
        if commit:
            instance.save()
        return instance


class PredictionCoreForm(_StyledPredictionFormMixin, forms.ModelForm):
    """Meme champs que PredictionForm, sans 'event' ni 'result' : utilise
    sur l'ecran unifie 'Nouveau pronostic' ou l'evenement est cree dans
    la meme soumission (event assigne et result mis a PENDING en vue)."""

    custom_platform_name = forms.CharField(
        max_length=100,
        required=False,
        label="Ou saisir le nom d'une nouvelle plateforme",
        help_text=(
            "Cree (ou reutilise) une plateforme recommandee a la volee, " "sans quitter cet ecran."
        ),
    )

    class Meta:
        model = Prediction
        fields = [
            "pick",
            "odds",
            "coupon_code",
            "confidence",
            "is_featured",
            "external_link",
            "custom_bet_url",
            "is_published",
        ]
        labels = {
            "pick": "Pronostic",
            "odds": "Cote (optionnel)",
            "coupon_code": "Code du coupon (optionnel)",
            "confidence": "Confiance % (optionnel)",
            "is_featured": "Match phare (Top matchs)",
            "external_link": "Plateforme de paris recommandee (optionnel)",
            "custom_bet_url": "Ou lien personnalise (optionnel)",
            "is_published": "Visible par les clients",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["external_link"].queryset = ExternalLink.objects.filter(category="platform")
        self.fields["external_link"].required = False
        self._apply_styles()

    def save(self, commit=True):
        instance = super().save(commit=False)
        platform_name = self.cleaned_data.get("custom_platform_name", "").strip()
        if platform_name and not instance.external_link_id:
            instance.external_link = _get_or_create_platform_link(
                platform_name, self.cleaned_data.get("custom_bet_url")
            )
        if commit:
            instance.save()
        return instance
