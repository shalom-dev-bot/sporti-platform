"""
Vue API publique : renvoie la configuration entreprise consultee par la
page d'accueil (logo, description, message d'accueil, liens externes).

Lecture seule et publique (pas d'authentification requise) : c'est ce
qu'un visiteur anonyme doit voir en arrivant sur la plateforme.
La modification de ces donnees se fait depuis le dashboard admin
(/gestion/), pas via cette API.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CompanyProfile, ExternalLink, WelcomeMessage
from .serializers import CompanyConfigSerializer


@api_view(["GET"])
def company_config(request):
    profile, _ = CompanyProfile.objects.get_or_create(pk=1)
    welcome_message = WelcomeMessage.objects.first()
    external_links = ExternalLink.objects.filter(is_active=True)

    data = {
        "profile": profile,
        "welcome_message": welcome_message,
        "external_links": external_links,
    }
    serializer = CompanyConfigSerializer(data, context={"request": request})
    return Response(serializer.data)
