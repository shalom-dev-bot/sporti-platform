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
# l'API-Football) -- la liste complete couverte par le plan gratuit de ce
# compte (verifie via /v4/competitions).
POPULAR_LEAGUES = [
    ("PL", "Premier League (Angleterre)"),
    ("ELC", "Championship (Angleterre)"),
    ("FL1", "Ligue 1 (France)"),
    ("PD", "La Liga (Espagne)"),
    ("SA", "Serie A (Italie)"),
    ("BL1", "Bundesliga (Allemagne)"),
    ("DED", "Eredivisie (Pays-Bas)"),
    ("PPL", "Primeira Liga (Portugal)"),
    ("BSA", "Serie A (Bresil)"),
    ("CL", "Ligue des Champions"),
    ("CLI", "Copa Libertadores"),
    ("EC", "Championnat d'Europe"),
    ("WC", "Coupe du Monde"),
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

    Important (plan gratuit) : l'endpoint "toutes competitions"
    (/v4/matches sans filtre) renvoie systematiquement une liste vide pour
    une seule journee -- il faut interroger chaque competition
    individuellement. Si aucun league_id n'est fourni, on boucle donc sur
    POPULAR_LEAGUES et on fusionne les resultats (une requete par
    competition, largement sous la limite de 10/minute du plan gratuit).

    Leve ApiFootballError si la cle est absente ou si l'appel echoue pour
    TOUTES les competitions ; une erreur isolee sur une seule competition
    (ex: quota atteint en cours de boucle) est ignoree pour ne pas faire
    echouer toute la recherche -- avec une nouvelle tentative avant
    d'abandonner, car un simple ralentissement reseau ponctuel sur UNE
    requete suffisait auparavant a faire disparaitre silencieusement
    toute une competition (ex: Ligue des Champions) des resultats,
    sans que l'admin ne s'en rende compte.
    """
    league_codes = [league_id] if league_id else [code for code, _label in POPULAR_LEAGUES]

    fixtures = []
    last_error = None
    remaining = None
    for code in league_codes:
        response = None
        for attempt in range(2):
            try:
                response = requests.get(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{code}/matches",
                    headers=_headers(),
                    params={"dateFrom": date_str, "dateTo": date_str},
                    timeout=15,
                )
                break
            except requests.RequestException as exc:
                last_error = f"Impossible de contacter football-data.org : {exc}"
        if response is None:
            continue

        remaining_header = response.headers.get("X-Requests-Available-Minute")
        if remaining_header is not None:
            remaining = int(remaining_header)

        payload = response.json()
        if response.status_code != 200:
            last_error = payload.get("message", f"code {response.status_code}")
            continue

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

    if not fixtures and last_error:
        raise ApiFootballError(f"Erreur football-data.org : {last_error}")

    fixtures.sort(key=lambda f: f["kickoff_at"] or "")

    quota = {"limit": 10, "remaining": remaining} if remaining is not None else None

    return fixtures, quota
