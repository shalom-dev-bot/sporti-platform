from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "dashboard"

urlpatterns = [
    path("connexion/", views.DashboardLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(next_page="/gestion/connexion/"), name="logout"),
    # Comme WhatsApp : l'ouverture de l'espace de gestion mene directement
    # aux conversations, pas aux statistiques.
    path(
        "",
        RedirectView.as_view(pattern_name="dashboard:conversations_list", permanent=False),
        name="home",
    ),
    path("statistiques/", views.dashboard_home, name="stats"),
    path("mot-de-passe/", views.change_password, name="change_password"),
    path("conversations/", views.conversations_list, name="conversations_list"),
    path(
        "conversations/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    path("entreprise/", views.company_settings, name="company_settings"),
    path("liens/", views.links_list, name="links_list"),
    path("liens/nouveau/", views.link_create, name="link_create"),
    path("liens/<int:link_id>/modifier/", views.link_edit, name="link_edit"),
    path("liens/<int:link_id>/supprimer/", views.link_delete, name="link_delete"),
]
