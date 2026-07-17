from django.contrib import admin

from .models import CompanyProfile, ExternalLink, WelcomeMessage


@admin.register(ExternalLink)
class ExternalLinkAdmin(admin.ModelAdmin):
    """Gestion des liens externes (WhatsApp, Telegram, etc.)."""

    list_display = ["platform", "label", "url", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["platform", "is_active"]
    search_fields = ["label", "url"]
    ordering = ["order"]


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_email", "contact_phone"]
    fieldsets = (
        ("Identite", {"fields": ("name", "logo", "cover_image")}),
        (
            "Description -- Francais",
            {"fields": ("description_fr",)},
        ),
        (
            "Description -- Anglais",
            {
                "fields": ("description_en",),
                "description": "Optionnel : si laisse vide, le francais sera utilise par defaut.",
            },
        ),
        ("Contact", {"fields": ("contact_email", "contact_phone")}),
    )


@admin.register(WelcomeMessage)
class WelcomeMessageAdmin(admin.ModelAdmin):
    list_display = ["updated_at", "is_text_enabled", "is_audio_enabled", "is_video_enabled"]
    fieldsets = (
        (
            "Message -- Francais",
            {"fields": ("text_fr",)},
        ),
        (
            "Message -- Anglais",
            {
                "fields": ("text_en",),
                "description": "Optionnel : si laisse vide, le francais sera utilise par defaut.",
            },
        ),
        ("Audio et video", {"fields": ("audio_file", "video_file")}),
        (
            "Activation",
            {"fields": ("is_text_enabled", "is_audio_enabled", "is_video_enabled")},
        ),
    )
