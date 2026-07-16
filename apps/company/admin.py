from django.contrib import admin

from .models import CompanyProfile, ExternalLink, WelcomeMessage


@admin.register(ExternalLink)
class ExternalLinkAdmin(admin.ModelAdmin):
    """Gestion des liens externes (WhatsApp, Telegram, etc.) -- cf. cahier
    des charges : l'administrateur doit pouvoir ajouter, modifier et
    supprimer ces liens facilement."""

    list_display = ["platform", "label", "url", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["platform", "is_active"]
    search_fields = ["label", "url"]
    ordering = ["order"]


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_email", "contact_phone"]


@admin.register(WelcomeMessage)
class WelcomeMessageAdmin(admin.ModelAdmin):
    list_display = ["updated_at", "is_text_enabled", "is_audio_enabled", "is_video_enabled"]
