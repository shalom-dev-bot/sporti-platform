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
    path("equipes/", views.teams_list, name="teams_list"),
    path("equipes/nouveau/", views.team_create, name="team_create"),
    path("equipes/<int:team_id>/modifier/", views.team_edit, name="team_edit"),
    path("equipes/<int:team_id>/supprimer/", views.team_delete, name="team_delete"),
    path("evenements/", views.events_list, name="events_list"),
    path("evenements/nouveau/", views.event_create, name="event_create"),
    path("evenements/<int:event_id>/modifier/", views.event_edit, name="event_edit"),
    path("evenements/<int:event_id>/supprimer/", views.event_delete, name="event_delete"),
    path("pronostics/", views.predictions_list, name="predictions_list"),
    path("pronostics/nouveau/", views.prediction_create, name="prediction_create"),
    path("pronostics/<int:prediction_id>/modifier/", views.prediction_edit, name="prediction_edit"),
    path(
        "pronostics/<int:prediction_id>/supprimer/",
        views.prediction_delete,
        name="prediction_delete",
    ),
    path("importer-matchs/", views.fixtures_search, name="fixtures_search"),
    path(
        "importer-matchs/<int:api_fixture_id>/importer/",
        views.fixture_import,
        name="fixture_import",
    ),
]
