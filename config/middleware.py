"""Sans ce middleware, LocaleMiddleware se sert de l'en-tete Accept-Language
envoye par le navigateur pour choisir la langue par defaut, ce qui affichait
le site en anglais pour les visiteurs dont le telephone/navigateur est
configure en anglais -- alors que la langue par defaut voulue est le
francais (LANGUAGE_CODE). Le bouton de bascule en haut du site reste
prioritaire : des qu'il est utilise, le cookie django_language est pose et
ce middleware laisse alors la main a Django normalement."""

from django.conf import settings


class ForceDefaultLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        if cookie_name not in request.COOKIES:
            request.META.pop("HTTP_ACCEPT_LANGUAGE", None)
        return self.get_response(request)
