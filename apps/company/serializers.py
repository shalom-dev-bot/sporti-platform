"""
Serializers DRF : transforment les modeles Company en JSON pour l'API,
et valident les donnees entrantes lors des modifications par l'admin.
"""

from rest_framework import serializers

from .models import CompanyProfile, ExternalLink, WelcomeMessage


class CompanyProfileSerializer(serializers.ModelSerializer):
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


class WelcomeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelcomeMessage
        fields = [
            "id",
            "text_fr",
            "text_en",
            "audio_file",
            "video_file",
            "is_text_enabled",
            "is_audio_enabled",
            "is_video_enabled",
        ]


class ExternalLinkSerializer(serializers.ModelSerializer):
    platform_label = serializers.CharField(source="get_platform_display", read_only=True)

    class Meta:
        model = ExternalLink
        fields = ["id", "platform", "platform_label", "label", "url", "is_active", "order"]


class CompanyConfigSerializer(serializers.Serializer):
    """Regroupe les 3 morceaux de config en une seule reponse pour la page d'accueil."""

    profile = CompanyProfileSerializer()
    welcome_message = WelcomeMessageSerializer(allow_null=True)
    external_links = ExternalLinkSerializer(many=True)
