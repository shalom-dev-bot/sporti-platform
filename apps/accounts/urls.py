from django.urls import path

from . import api_views, views

app_name = "accounts"

urlpatterns = [
    path("api/push/subscribe/", api_views.PushSubscribeView.as_view(), name="push_subscribe"),
    path("profil/", views.profile, name="profile"),
]
