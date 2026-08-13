"""
Formulaires du dashboard admin pour piloter l'identite entreprise, le
message d'accueil et les liens externes -- le CRUD demande par le client.
"""

from django import forms

from .models import CompanyProfile, ExternalLink, WelcomeMessage


class _StyledFormMixin:
    """Applique les classes CSS du design system a tous les champs,
    sauf les cases a cocher qui gardent leur propre style."""

    def _apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, (forms.CheckboxInput,)):
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
                    {"class": "field-input", "rows": field.widget.attrs.get("rows", 4)}
                )
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "field-input"})
            else:
                field.widget.attrs.update({"class": "field-input"})


class CompanyProfileForm(_StyledFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "name",
            "logo",
            "description_fr",
            "description_en",
            "contact_email",
            "contact_phone",
        ]
        labels = {
            "name": "Nom de l'entreprise",
            "logo": "Logo",
            "description_fr": "Description (français)",
            "description_en": "Description (anglais)",
            "contact_email": "E-mail de contact",
            "contact_phone": "Téléphone de contact",
        }
        # ClearableFileInput affiche "Currently: <fichier> Clear" en texte
        # brut des qu'un logo existe deja -- l'UI custom gere deja ca.
        widgets = {"logo": forms.FileInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class WelcomeTextForm(_StyledFormMixin, forms.ModelForm):
    """Formulaire separe du vocal : partager un seul WelcomeMessageForm pour
    les deux <form> HTML distinctes faisait echouer la sauvegarde du vocal,
    car text_fr (obligatoire) n'est jamais soumis par le formulaire vocal."""

    class Meta:
        model = WelcomeMessage
        fields = ["text_fr", "text_en", "is_text_enabled"]
        labels = {
            "text_fr": "Message (français)",
            "text_en": "Message (anglais)",
            "is_text_enabled": "Afficher le message texte",
        }
        widgets = {
            "text_fr": forms.Textarea(attrs={"rows": 2}),
            "text_en": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class WelcomeAudioForm(_StyledFormMixin, forms.ModelForm):
    class Meta:
        model = WelcomeMessage
        fields = ["audio_file", "is_audio_enabled"]
        labels = {
            "audio_file": "Fichier audio",
            "is_audio_enabled": "Afficher le message vocal",
        }
        # ClearableFileInput affiche "Currently: <fichier> Clear" en texte
        # brut des qu'un vocal existe deja -- l'UI custom gere deja ca.
        widgets = {"audio_file": forms.FileInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class ExternalLinkForm(_StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ExternalLink
        fields = ["category", "platform", "label", "url", "promo_code", "is_active", "order"]
        labels = {
            "category": "Catégorie",
            "platform": "Plateforme",
            "label": "Libellé (optionnel)",
            "url": "Lien",
            "promo_code": "Code promo (optionnel)",
            "is_active": "Visible sur la page d'accueil",
            "order": "Ordre d'affichage",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()
