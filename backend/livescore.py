"""
Synchronisation automatique des scores en direct depuis une API externe.

Deux fournisseurs supportés (variable d'env LIVESCORE_PROVIDER) :
- "zafronix" (par défaut) : https://api.zafronix.com - Coupe du Monde 2026,
  un seul appel récupère tous les matchs (économise le quota gratuit
  250 requêtes/jour). Clé via ZAFRONIX_API_KEY (header X-API-Key).
  /!\\ Le plan gratuit Zafronix ne fournit PAS le statut "live" en temps réel
  (pas de flux SSE / pas de mise à jour live) - seuls les scores finalisés
  remontent (avec un délai). On traite donc tout match avec un score non nul
  comme "finished".
- "api_football" : api-sports.io / RapidAPI (ancienne intégration), nécessite
  API_FOOTBALL_KEY.

Fonctionnement :
- `sync_live_scores(db)` interroge l'API, fait correspondre chaque fixture à
  un match de `db.matches` via le nom des équipes, puis met à jour
  `home_score_actual`, `away_score_actual` et `status`.
- Si le statut passe à "finished", on déclenche le recalcul des points et la
  propagation du vainqueur en phase éliminatoire (mêmes fonctions que
  l'endpoint /admin/match-result).
- Une tâche de fond (voir server.py) appelle cette fonction périodiquement,
  uniquement s'il existe au moins un match "scheduled" ou "live" dans une
  fenêtre proche de l'heure actuelle (pour économiser le quota API gratuit).
"""
import os
import logging
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LIVESCORE_PROVIDER = os.environ.get("LIVESCORE_PROVIDER", "zafronix").lower()

# ------------------------------------------------------------------
# Config Zafronix (https://api.zafronix.com)
# ------------------------------------------------------------------
ZAFRONIX_API_KEY = os.environ.get("ZAFRONIX_API_KEY", "")
ZAFRONIX_BASE_URL = os.environ.get("ZAFRONIX_BASE_URL", "https://api.zafronix.com/fifa/worldcup/v1")
ZAFRONIX_YEAR = int(os.environ.get("ZAFRONIX_YEAR", "2026"))

# ------------------------------------------------------------------
# Config API-Football (api-sports.io)
# ------------------------------------------------------------------
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io")
WC_LEAGUE_ID = int(os.environ.get("API_FOOTBALL_LEAGUE_ID", "1"))
WC_SEASON = int(os.environ.get("API_FOOTBALL_SEASON", "2026"))

# ------------------------------------------------------------------
# Config football-data.org (https://www.football-data.org)
# ------------------------------------------------------------------
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE_URL = os.environ.get("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4")
FOOTBALL_DATA_COMPETITION = os.environ.get("FOOTBALL_DATA_COMPETITION", "WC")


LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"}
FINISHED_STATUSES = {"FT", "AET", "PEN", "AWD", "WO"}
NOT_STARTED_STATUSES = {"NS", "TBD", "PST"}

# Statuts football-data.org : SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED,
# POSTPONED, SUSPENDED, CANCELLED
FOOTBALL_DATA_LIVE_STATUSES = {"IN_PLAY", "PAUSED"}
FOOTBALL_DATA_FINISHED_STATUSES = {"FINISHED", "AWARDED"}


def is_configured() -> bool:
    if LIVESCORE_PROVIDER == "zafronix":
        return bool(ZAFRONIX_API_KEY)
    if LIVESCORE_PROVIDER == "api_football":
        return bool(API_FOOTBALL_KEY)
    if LIVESCORE_PROVIDER == "football_data":
        return bool(FOOTBALL_DATA_API_KEY)
    return False


# ------------------------------------------------------------------
# Mapping noms FR (fixtures.py) -> noms EN utilisés par les API externes
# ------------------------------------------------------------------
TEAM_NAME_MAP = {
    "Mexique": "Mexico",
    "Afrique du Sud": "South Africa",
    "Corée du Sud": "South Korea",
    "Tchéquie": "Czechia",
    "Canada": "Canada",
    "Bosnie-Herzégovine": "Bosnia and Herzegovina",
    "Qatar": "Qatar",
    "Suisse": "Switzerland",
    "Brésil": "Brazil",
    "Maroc": "Morocco",
    "Haïti": "Haiti",
    "Écosse": "Scotland",
    "États-Unis": "USA",
    "Paraguay": "Paraguay",
    "Australie": "Australia",
    "Turquie": "Turkey",
    "Allemagne": "Germany",
    "Curaçao": "Curacao",
    "Côte d'Ivoire": "Ivory Coast",
    "Équateur": "Ecuador",
    "Pays-Bas": "Netherlands",
    "Japon": "Japan",
    "Suède": "Sweden",
    "Tunisie": "Tunisia",
    "Belgique": "Belgium",
    "Égypte": "Egypt",
    "Iran": "IR Iran",
    "Nouvelle-Zélande": "New Zealand",
    "Espagne": "Spain",
    "Cap-Vert": "Cape Verde",
    "Arabie saoudite": "Saudi Arabia",
    "Uruguay": "Uruguay",
    "France": "France",
    "Sénégal": "Senegal",
    "Irak": "Iraq",
    "Norvège": "Norway",
    "Argentine": "Argentina",
    "Algérie": "Algeria",
    "Autriche": "Austria",
    "Jordanie": "Jordan",
    "Portugal": "Portugal",
    "RD Congo": "DR Congo",
    "Ouzbékistan": "Uzbekistan",
    "Colombie": "Colombia",
    "Angleterre": "England",
    "Croatie": "Croatia",
    "Ghana": "Ghana",
    "Panama": "Panama",
}
# Mapping inverse (nom EN -> nom FR utilisé en base) - pour API-Football
NAME_MAP_REVERSE = {v: k for k, v in TEAM_NAME_MAP.items()}


def _normalize_name(s: str) -> str:
    """minuscule, sans accents, sans espaces/ponctuation - pour comparer
    des noms d'équipes venant de sources différentes."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


# Variantes de noms supplémentaires (utilisées notamment par Zafronix, qui
# garde parfois les noms avec accents/orthographe FIFA différente d'API-Football)
EXTRA_NAME_VARIANTS = {
    "Tchéquie": ["Czech Republic", "Czechia", "Tchéquie", "Tchequie"],
    "RD Congo": ["DR Congo", "Congo DR", "Democratic Republic of the Congo", "DR Congo (Zaire)", "Congo, DR"],
    "Côte d'Ivoire": ["Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast"],
    "Corée du Sud": ["South Korea", "Korea Republic", "Korea, South", "Korea Republic (South Korea)"],
    "États-Unis": ["USA", "United States", "United States of America", "USMNT"],
    "Iran": ["IR Iran", "Iran", "Islamic Republic of Iran", "IR Iran (Islamic Republic of Iran)"],
    "Curaçao": ["Curacao", "Curaçao"],
    "Cap-Vert": ["Cape Verde", "Cabo Verde", "Cape Verde Islands"],
    "Turquie": ["Turkey", "Türkiye", "Turkiye"],
    "Bosnie-Herzégovine": ["Bosnia and Herzegovina", "Bosnia-Herzegovina", "Bosnia & Herzegovina"],
}

# Index normalisé -> nom FR (utilisé en base) pour résoudre les noms venant
# de n'importe quel fournisseur externe.
_NAME_INDEX: dict[str, str] = {}
for _fr, _en in TEAM_NAME_MAP.items():
    _NAME_INDEX[_normalize_name(_fr)] = _fr
    _NAME_INDEX[_normalize_name(_en)] = _fr
for _fr, _variants in EXTRA_NAME_VARIANTS.items():
    for _v in _variants:
        _NAME_INDEX[_normalize_name(_v)] = _fr


def _resolve_team_fr(api_name: Optional[str]) -> Optional[str]:
    if not api_name:
        return None
    return _NAME_INDEX.get(_normalize_name(api_name))


# ------------------------------------------------------------------
# Zafronix
# ------------------------------------------------------------------
async def _fetch_fixtures_zafronix() -> list[dict]:
    """Récupère tous les matchs WC2026 en un seul appel (économise le quota)."""
    if not ZAFRONIX_API_KEY:
        logger.warning("ZAFRONIX_API_KEY non configurée - sync ignorée")
        return []

    url = f"{ZAFRONIX_BASE_URL}/matches"
    params = {"year": ZAFRONIX_YEAR, "denormalize": "true"}
    headers = {"X-API-Key": ZAFRONIX_API_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"DEBUG: Contenu brut de l'API: {data}")
        except Exception as e:
            logger.error(f"Erreur appel Zafronix: {e}")
            return []

    raw_matches = data.get("data") if isinstance(data, dict) else data
    if not isinstance(raw_matches, list):
        raw_matches = []

    normalized = []
    for m in raw_matches:
        home = m.get("homeTeam") or m.get("home_team") or m.get("home")
        away = m.get("awayTeam") or m.get("away_team") or m.get("away")
        home_score = m.get("homeScore", m.get("home_score"))
        away_score = m.get("awayScore", m.get("away_score"))

        raw_status = str(m.get("status") or "").lower()
        is_finished_flag = m.get("finalized") or m.get("finished") or m.get("is_finished")

        if raw_status in ("live", "in_play", "in_progress", "1h", "2h", "ht"):
            status = "live"
        elif raw_status in ("finished", "final", "ft", "completed") or is_finished_flag:
            status = "finished"
        elif home_score is not None and away_score is not None and (home_score > 0 or away_score > 0):
            status = "finished"
        elif home_score is not None and away_score is not None:
            kickoff = m.get("kickoffTime") or m.get("date") or m.get("matchDate") or ""
            if kickoff and kickoff < datetime.now(timezone.utc).isoformat():
                status = "finished"
            else:
                status = "scheduled"
        else:
            status = "scheduled"

        penalties = m.get("penalties") or {}
        normalized.append({
            "home": home,
            "away": away,
            "home_score": home_score,
            "away_score": away_score,
            "status": status,
            "penalty_home": penalties.get("home"),
            "penalty_away": penalties.get("away"),
        })
    return normalized


# ------------------------------------------------------------------
# API-Football
# ------------------------------------------------------------------
def _af_headers() -> dict:
    if "rapidapi" in API_FOOTBALL_HOST:
        return {
            "x-rapidapi-key": API_FOOTBALL_KEY,
            "x-rapidapi-host": API_FOOTBALL_HOST,
        }
    return {"x-apisports-key": API_FOOTBALL_KEY}


def _map_af_status(short: str) -> Optional[str]:
    if short in FINISHED_STATUSES:
        return "finished"
    if short in LIVE_STATUSES:
        return "live"
    if short in NOT_STARTED_STATUSES:
        return "scheduled"
    return None


async def _fetch_fixtures_for_date_api_football(date_str: str) -> list[dict]:
    if not API_FOOTBALL_KEY:
        return []

    url = f"https://{API_FOOTBALL_HOST}/fixtures"
    params = {"league": WC_LEAGUE_ID, "season": WC_SEASON, "date": date_str}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params, headers=_af_headers())
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Erreur appel API-Football: {e}")
            return []

    return data.get("response", [])


async def _fetch_fixtures_api_football() -> list[dict]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    fixtures = []
    for d in (yesterday, today):
        fixtures.extend(await _fetch_fixtures_for_date_api_football(d))

    normalized = []
    for fixture in fixtures:
        status_short = fixture.get("fixture", {}).get("status", {}).get("short")
        new_status = _map_af_status(status_short)
        if new_status is None:
            continue

        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})
        penalties = fixture.get("score", {}).get("penalty", {})
        normalized.append({
            "home": teams.get("home", {}).get("name"),
            "away": teams.get("away", {}).get("name"),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "status": new_status,
            "penalty_home": penalties.get("home"),
            "penalty_away": penalties.get("away"),
        })
    return normalized


# ------------------------------------------------------------------
# football-data.org (https://api.football-data.org)
# ------------------------------------------------------------------
async def _fetch_fixtures_football_data() -> list[dict]:
    """Récupère tous les matchs de la compétition (Coupe du Monde) en un
    seul appel. Plan gratuit : 10 req/min, scores légèrement différés."""
    if not FOOTBALL_DATA_API_KEY:
        logger.warning("FOOTBALL_DATA_API_KEY non configurée - sync ignorée")
        return []

    url = f"{FOOTBALL_DATA_BASE_URL}/competitions/{FOOTBALL_DATA_COMPETITION}/matches"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Erreur appel football-data.org: {e}")
            return []

    raw_matches = data.get("matches") if isinstance(data, dict) else None
    if not isinstance(raw_matches, list):
        raw_matches = []

    normalized = []
    for m in raw_matches:
        raw_status = str(m.get("status") or "").upper()
        if raw_status in FOOTBALL_DATA_FINISHED_STATUSES:
            status = "finished"
        elif raw_status in FOOTBALL_DATA_LIVE_STATUSES:
            status = "live"
        else:
            status = "scheduled"

        score = m.get("score") or {}
        full_time = score.get("fullTime") or {}
        half_time = score.get("halfTime") or {}
        penalties = score.get("penalties") or {}

        home_score = full_time.get("home")
        away_score = full_time.get("away")
        # À la mi-temps (et plus généralement en live), football-data.org ne
        # remplit "fullTime" qu'à la fin du match : on retombe sur
        # "halfTime" pour que le score en cours soit déjà visible.
        if home_score is None and away_score is None:
            home_score = half_time.get("home")
            away_score = half_time.get("away")

        normalized.append({
            "home": (m.get("homeTeam") or {}).get("name"),
            "away": (m.get("awayTeam") or {}).get("name"),
            "home_score": home_score,
            "away_score": away_score,
            "status": status,
            "penalty_home": penalties.get("home"),
            "penalty_away": penalties.get("away"),
        })
    return normalized


# ------------------------------------------------------------------
# Logique commune
# ------------------------------------------------------------------
async def _fetch_normalized_fixtures() -> list[dict]:
    if LIVESCORE_PROVIDER == "api_football":
        return await _fetch_fixtures_api_football()
    if LIVESCORE_PROVIDER == "football_data":
        return await _fetch_fixtures_football_data()
    return await _fetch_fixtures_zafronix()


async def has_relevant_matches(db, window_hours: float = 24.0) -> bool:
    """
    Vrai s'il existe un match 'scheduled' ou 'live' dont le coup d'envoi est
    proche de maintenant (déjà commencé depuis moins de window_hours, ou
    démarre dans moins de 30 minutes), ou déjà 'live'.
    Permet d'éviter d'appeler l'API en dehors des créneaux de match, tout en
    laissant le temps au fournisseur (Zafronix plan gratuit) de remonter le
    score final avec un certain délai après le coup d'envoi.
    """
    now = datetime.now(timezone.utc)

    if await db.matches.count_documents({"status": "live"}) > 0:
        return True

    lower = (now - timedelta(hours=window_hours)).isoformat()
    upper = (now + timedelta(minutes=30)).isoformat()
    count = await db.matches.count_documents({
        "status": "scheduled",
        "kickoff_utc": {"$gte": lower, "$lte": upper},
    })
    return count > 0


async def sync_live_scores(db, recalculate_match_points, propagate_knockout_winner) -> dict:
    """
    Synchronise les scores depuis le fournisseur configuré (LIVESCORE_PROVIDER).
    `recalculate_match_points` et `propagate_knockout_winner` sont passées en
    paramètre pour réutiliser exactement la même logique que
    POST /admin/match-result.
    """
    fixtures = await _fetch_normalized_fixtures()
    logger.info(f"DEBUG: Fixtures reçues : {fixtures}")

    updated = []
    for fixture in fixtures:
        new_status = fixture.get("status")
        if new_status not in ("live", "finished"):
            continue

        home_goals = fixture.get("home_score")
        away_goals = fixture.get("away_score")
        if home_goals is None or away_goals is None:
            continue

        home_fr = _resolve_team_fr(fixture.get("home"))
        away_fr = _resolve_team_fr(fixture.get("away"))
        if not home_fr or not away_fr:
            logger.warning(f"DEBUG: Mapping impossible pour {fixture.get('home')} vs {fixture.get('away')}")
            continue

        match = await db.matches.find_one({
            "home_team": home_fr,
            "away_team": away_fr,
            "status": {"$ne": "finished"},
        })
        if not match:
            continue

        if (
            match.get("status") == new_status
            and match.get("home_score_actual") == home_goals
            and match.get("away_score_actual") == away_goals
        ):
            continue  # rien de changé

        update = {
            "home_score_actual": home_goals,
            "away_score_actual": away_goals,
            "status": new_status,
        }

        # Tirs au but (phase éliminatoire) : si égalité au score final
        if new_status == "finished" and home_goals == away_goals and match.get("phase") == "knockout":
            ph, pa = fixture.get("penalty_home"), fixture.get("penalty_away")
            if ph is not None and pa is not None:
                update["winner_side"] = "home" if ph > pa else "away"

        await db.matches.update_one({"id": match["id"]}, {"$set": update})

        if new_status == "finished":
            await recalculate_match_points(match["id"])
            if match.get("phase") == "knockout":
                await propagate_knockout_winner(match["id"])

        updated.append({
            "match_id": match["id"],
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "score": f"{home_goals}-{away_goals}",
            "status": new_status,
        })

    return {"checked": len(fixtures), "updated": updated}
