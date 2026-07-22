from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("connexion/", views.DashboardLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(next_page="/gestion/connexion/"), name="logout"),
    path("", views.dashboard_home, name="home"),
    path("mot-de-passe/", views.change_password, name="change_password"),
    path("conversations/", views.conversations_list, name="conversations_list"),
    path(
        "conversations/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
]
