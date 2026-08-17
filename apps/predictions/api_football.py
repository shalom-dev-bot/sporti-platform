"""
Client pour l'API-Football (v3.football.api-sports.io). Une seule
responsabilite : interroger l'API et renvoyer des donnees Python
simples (dicts), sans toucher a la base de donnees -- l'import en
base se fait dans apps.dashboard.views.

Necessite API_FOOTBALL_KEY dans les settings (voir .env.example).
Compte gratuit sur https://dashboard.api-football.com -- le plan
gratuit est limite en nombre de requetes par jour, donc chaque
recherche admin ne declenche qu'un seul appel API.
"""

from django.conf import settings

import requests

# Quelques competitions populaires pour faciliter la recherche depuis
# le dashboard (id API-Football : nom affiche). Liste volontairement
# courte -- l'admin peut aussi saisir un autre id directement.
POPULAR_LEAGUES = [
    (39, "Premier League (Angleterre)"),
    (61, "Ligue 1 (France)"),
    (140, "La Liga (Espagne)"),
    (135, "Serie A (Italie)"),
    (78, "Bundesliga (Allemagne)"),
    (2, "Ligue des Champions"),
    (3, "Ligue Europa"),
    (848, "Conference League"),
]


class ApiFootballError(Exception):
    """Erreur lors de l'appel a l'API-Football (cle manquante, quota
    depasse, reponse invalide, etc.)."""


def _headers():
    if not settings.API_FOOTBALL_KEY:
        raise ApiFootballError(
            "Aucune cle API-Football configuree (API_FOOTBALL_KEY dans le .env)."
        )
    return {"x-apisports-key": settings.API_FOOTBALL_KEY}


def search_fixtures(date_str, league_id=None, season=None):
    """Recupere les matchs pour une date donnee (YYYY-MM-DD), filtres
    par competition si league_id est fourni. Renvoie une liste de
    dicts normalises, triee par heure de coup d'envoi.

    Leve ApiFootballError si la cle est absente ou si l'appel echoue
    (apres une nouvelle tentative, un simple ralentissement reseau
    ponctuel ne doit pas suffire a faire echouer toute la recherche).
    """
    params = {"date": date_str}
    if league_id:
        params["league"] = league_id
        params["season"] = season or int(date_str[:4])

    response = None
    last_exc = None
    for attempt in range(2):
        try:
            response = requests.get(
                f"{settings.API_FOOTBALL_BASE_URL}/fixtures",
                headers=_headers(),
                params=params,
                timeout=15,
            )
            break
        except requests.RequestException as exc:
            last_exc = exc
    if response is None:
        raise ApiFootballError(f"Impossible de contacter l'API-Football : {last_exc}") from last_exc

    if response.status_code != 200:
        raise ApiFootballError(f"L'API-Football a repondu avec le code {response.status_code}.")

    payload = response.json()
    errors = payload.get("errors")
    if errors:
        # L'API renvoie parfois un dict, parfois une liste, selon l'erreur.
        message = errors if isinstance(errors, str) else str(errors)
        raise ApiFootballError(f"Erreur API-Football : {message}")

    fixtures = []
    for item in payload.get("response", []):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        if not (fixture.get("id") and home.get("id") and away.get("id")):
            continue

        fixtures.append(
            {
                "api_id": fixture["id"],
                "kickoff_at": fixture.get("date"),
                "status_short": fixture.get("status", {}).get("short", ""),
                "competition": f"{league.get('name', '')} ({league.get('country', '')})".strip(),
                "home_id": home["id"],
                "home_name": home.get("name", ""),
                "home_logo": home.get("logo", ""),
                "away_id": away["id"],
                "away_name": away.get("name", ""),
                "away_logo": away.get("logo", ""),
            }
        )

    fixtures.sort(key=lambda f: f["kickoff_at"] or "")

    quota = None
    limit_header = response.headers.get("x-ratelimit-requests-limit")
    remaining_header = response.headers.get("x-ratelimit-requests-remaining")
    if limit_header is not None and remaining_header is not None:
        quota = {"limit": int(limit_header), "remaining": int(remaining_header)}

    return fixtures, quota
