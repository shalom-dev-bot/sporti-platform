"""
Serializers DRF : transforment les modeles Company en JSON pour l'API,
et valident les donnees entrantes lors des modifications par l'admin.
"""

from rest_framework import serializers

from .models import CompanyProfile, ExternalLink, WelcomeMessage


class CompanyProfileSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "name",
            "logo",
            "cover_image",
            "description",
            "contact_email",
            "contact_phone",
        ]

    def get_description(self, obj):
        """Renvoie la description dans la langue active de la requete
        (definie par i18n_patterns / LocaleMiddleware)."""
        request = self.context.get("request")
        language_code = getattr(request, "LANGUAGE_CODE", "fr") if request else "fr"
        return obj.get_description(language_code)


class WelcomeMessageSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()

    class Meta:
        model = WelcomeMessage
        fields = [
            "id",
            "text",
            "audio_file",
            "video_file",
            "is_text_enabled",
            "is_audio_enabled",
            "is_video_enabled",
        ]

    def get_text(self, obj):
        request = self.context.get("request")
        language_code = getattr(request, "LANGUAGE_CODE", "fr") if request else "fr"
        return obj.get_text(language_code)


class ExternalLinkSerializer(serializers.ModelSerializer):
    platform_label = serializers.CharField(source="get_platform_display", read_only=True)

    class Meta:
        model = ExternalLink
        fields = [
            "id",
            "category",
            "platform",
            "platform_label",
            "label",
            "url",
            "promo_code",
            "is_active",
            "order",
        ]


class CompanyConfigSerializer(serializers.Serializer):
    """Regroupe les 3 morceaux de config en une seule reponse pour la page d'accueil."""

    profile = CompanyProfileSerializer()
    welcome_message = WelcomeMessageSerializer(allow_null=True)
    external_links = ExternalLinkSerializer(many=True)
