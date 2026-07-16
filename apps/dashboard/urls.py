from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("connexion/", views.DashboardLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(next_page="/gestion/connexion/"), name="logout"),
    path("", views.dashboard_home, name="home"),
]
