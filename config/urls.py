"""Routage principal du projet SPORTI."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
