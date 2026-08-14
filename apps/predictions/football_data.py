"""
Client pour football-data.org (v4) -- alternative gratuite a l'API-Football
quand le budget ne permet pas un plan payant. Meme interface publique que
apps.predictions.api_football (search_fixtures, ApiFootballError,
POPULAR_LEAGUES) pour rester un remplacement direct cote vues/templates.

Contrairement au plan gratuit d'API-Football, le plan gratuit de
football-data.org donne acces a la saison EN COURS (pas seulement a des
saisons passees), mais uniquement pour un nombre limite de competitions
(les plus grandes ligues europeennes) et avec une limite de 10 requetes
par minute.

Cle gratuite a obtenir sur https://www.football-data.org/client/register,
puis a renseigner dans FOOTBALL_DATA_API_KEY (.env local + variables Railway).
"""

from django.conf import settings

import requests

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

# Codes de competition football-data.org (pas les memes identifiants que
# l'API-Football) -- limite aux competitions couvertes par le plan gratuit.
POPULAR_LEAGUES = [
    ("PL", "Premier League (Angleterre)"),
    ("ELC", "Championship (Angleterre)"),
    ("FL1", "Ligue 1 (France)"),
    ("PD", "La Liga (Espagne)"),
    ("SA", "Serie A (Italie)"),
    ("BL1", "Bundesliga (Allemagne)"),
    ("DED", "Eredivisie (Pays-Bas)"),
    ("PPL", "Primeira Liga (Portugal)"),
    ("CL", "Ligue des Champions"),
]

_STATUS_MAP = {
    "SCHEDULED": "NS",
    "TIMED": "NS",
    "IN_PLAY": "1H",
    "PAUSED": "HT",
    "LIVE": "1H",
    "FINISHED": "FT",
    "SUSPENDED": "PST",
    "POSTPONED": "PST",
    "CANCELLED": "CANC",
    "AWARDED": "FT",
}


class ApiFootballError(Exception):
    """Erreur lors de l'appel a football-data.org (cle manquante, quota
    depasse, reponse invalide, etc.)."""


def _headers():
    if not settings.FOOTBALL_DATA_API_KEY:
        raise ApiFootballError(
            "Aucune cle football-data.org configuree (FOOTBALL_DATA_API_KEY dans le .env)."
        )
    return {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}


def search_fixtures(date_str, league_id=None, season=None):
    """Recupere les matchs pour une date donnee (YYYY-MM-DD), filtres par
    competition si league_id (code football-data, ex: "PL") est fourni.
    Renvoie une liste de dicts normalises (meme forme que api_football),
    triee par heure de coup d'envoi.

    Leve ApiFootballError si la cle est absente ou si l'appel echoue.
    """
    params = {"dateFrom": date_str, "dateTo": date_str}
    if league_id:
        url = f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_id}/matches"
    else:
        url = f"{FOOTBALL_DATA_BASE_URL}/matches"

    try:
        response = requests.get(url, headers=_headers(), params=params, timeout=10)
    except requests.RequestException as exc:
        raise ApiFootballError(f"Impossible de contacter football-data.org : {exc}") from exc

    payload = response.json()
    if response.status_code != 200:
        message = payload.get("message", f"code {response.status_code}")
        raise ApiFootballError(f"Erreur football-data.org : {message}")

    fixtures = []
    for match in payload.get("matches", []):
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        competition = match.get("competition") or {}

        if not (match.get("id") and home.get("id") and away.get("id")):
            continue

        fixtures.append(
            {
                "api_id": match["id"],
                "kickoff_at": match.get("utcDate"),
                "status_short": _STATUS_MAP.get(match.get("status", ""), ""),
                "competition": competition.get("name", ""),
                "home_id": home["id"],
                "home_name": home.get("name") or home.get("shortName") or "",
                "home_logo": home.get("crest", ""),
                "away_id": away["id"],
                "away_name": away.get("name") or away.get("shortName") or "",
                "away_logo": away.get("crest", ""),
            }
        )

    fixtures.sort(key=lambda f: f["kickoff_at"] or "")

    quota = None
    remaining_header = response.headers.get("X-Requests-Available-Minute")
    if remaining_header is not None:
        quota = {"limit": 10, "remaining": int(remaining_header)}

    return fixtures, quota
