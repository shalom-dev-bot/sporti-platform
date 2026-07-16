from django.urls import path

from . import api_views

app_name = "company"

urlpatterns = [
    path("api/config/", api_views.company_config, name="api_config"),
]
