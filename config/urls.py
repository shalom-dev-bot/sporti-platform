"""Routage principal du projet SPORTI."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_static

from apps.chat import views as chat_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("entreprise/", include("apps.company.urls")),
    path("gestion/", include("apps.dashboard.urls")),
    path("comptes/", include("apps.accounts.urls")),
    path("service-worker.js", chat_views.service_worker, name="service_worker"),
    path("offline/", chat_views.offline, name="offline"),
]

urlpatterns += i18n_patterns(
    path("pronostics/", include("apps.predictions.urls")),
    path("", include("apps.chat.urls")),
)


# Django's own `static()` helper is a no-op unless DEBUG=True, ce qui
# laissait /media/ totalement non servi en production (STORAGE_BACKEND
# "local" tant que S3 n'est pas configure) -- avatars, images et vocaux
# echouaient tous silencieusement (404), meme fraichement envoyes.
# Acceptable pour ce volume de demo ; a retirer si/quand STORAGE_BACKEND
# passe sur "s3".
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve_static, {"document_root": settings.MEDIA_ROOT}),
]
