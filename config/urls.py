"""Routage principal du projet SPORTI."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("entreprise/", include("apps.company.urls")),
    path("gestion/", include("apps.dashboard.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("apps.chat.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
