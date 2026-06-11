"""
Backend FastAPI - Application de pronostics Coupe du Monde 2026.
- Auth JWT (email/pseudo/password) - bcrypt
- MongoDB (motor) - 3 collections : users, matches, predictions
- Calculateur de points sur passage d'un match au statut "finished"
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict

from fixtures import build_group_stage_matches, build_knockout_matches

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'change-me')

app = FastAPI(title="WC2026 Pronostics API")
api = APIRouter(prefix="/api")
bearer_scheme = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers Auth
# ------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, pseudo: str) -> str:
    payload = {
        "sub": user_id,
        "pseudo": pseudo,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "pin_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


# ------------------------------------------------------------------
# Modèles Pydantic
# ------------------------------------------------------------------
class RegisterIn(BaseModel):
    pseudo: str = Field(min_length=2, max_length=30)
    pin: str = Field(pattern=r"^\d{4,6}$")


class LoginIn(BaseModel):
    pseudo: str
    pin: str


class UserOut(BaseModel):
    id: str
    pseudo: str
    total_points: int = 0
    created_at: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


class PredictionIn(BaseModel):
    match_id: str
    home_score_predicted: int = Field(ge=0, le=99)
    away_score_predicted: int = Field(ge=0, le=99)


class PredictionOut(BaseModel):
    id: str
    user_id: str
    match_id: str
    home_score_predicted: int
    away_score_predicted: int
    points_earned: int = 0


class MatchOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    home_team: str
    home_code: str
    away_team: str
    away_code: str
    group: str
    matchday: int
    kickoff_utc: str
    display_date: str
    kickoff_hour_paris: int
    broadcast_channels: str
    status: Literal["scheduled", "live", "finished"]
    home_score_actual: Optional[int] = None
    away_score_actual: Optional[int] = None
    phase: str = "group"
    round: Optional[str] = None
    round_label: Optional[str] = None


class MatchResultIn(BaseModel):
    match_id: str
    home_score_actual: int = Field(ge=0, le=99)
    away_score_actual: int = Field(ge=0, le=99)
    status: Literal["live", "finished"] = "finished"
    # Pour les matchs à élimination directe terminés sur égalité (tirs au but)
    winner: Optional[Literal["home", "away"]] = None


class MatchTeamsIn(BaseModel):
    """Mise à jour des équipes d'un match (utile pour la phase éliminatoire)."""
    match_id: str
    home_team: Optional[str] = Field(default=None, min_length=1, max_length=60)
    home_code: Optional[str] = Field(default=None, max_length=10)
    away_team: Optional[str] = Field(default=None, min_length=1, max_length=60)
    away_code: Optional[str] = Field(default=None, max_length=10)


class LeaderboardEntry(BaseModel):
    rank: int
    pseudo: str
    total_points: int


# ------------------------------------------------------------------
# Calculateur de points
# ------------------------------------------------------------------
def compute_points(
    home_pred: int, away_pred: int, home_actual: int, away_actual: int
) -> int:
    """
    - Bon résultat (1N2) : +1
    - Score exact :        +3 bonus (en plus du +1 résultat)
    - Bonne diff. de buts : +1 bonus
    """
    points = 0

    def outcome(h, a):
        if h > a:
            return "H"
        if h < a:
            return "A"
        return "D"

    if outcome(home_pred, away_pred) == outcome(home_actual, away_actual):
        points += 1
        if (home_pred - away_pred) == (home_actual - away_actual):
            points += 1
        if home_pred == home_actual and away_pred == away_actual:
            points += 3
    return points


async def recalculate_match_points(match_id: str):
    """À appeler quand le score réel d'un match change ou passe à 'finished'."""
    match = await db.matches.find_one({"id": match_id}, {"_id": 0})
    if not match or match.get("status") != "finished":
        return
    ha = match["home_score_actual"]
    aa = match["away_score_actual"]
    if ha is None or aa is None:
        return

    cursor = db.predictions.find({"match_id": match_id})
    async for pred in cursor:
        new_points = compute_points(
            pred["home_score_predicted"], pred["away_score_predicted"], ha, aa
        )
        if new_points != pred.get("points_earned", 0):
            delta = new_points - pred.get("points_earned", 0)
            await db.predictions.update_one(
                {"id": pred["id"]}, {"$set": {"points_earned": new_points}}
            )
            await db.users.update_one(
                {"id": pred["user_id"]}, {"$inc": {"total_points": delta}}
            )


# Bracket d'élimination directe : map (round, matchday) -> { next round, slot, role }
# role = "winner" pour SF→Finale et tours précédents, mais SF a aussi un loser→3RD.
def _next_slot_for(round_key: str, md: int) -> Optional[dict]:
    """
    Retourne {next_round, next_md, slot} pour le VAINQUEUR.
    Renvoie None si pas de tour suivant (Finale, 3e place).
    """
    if round_key == "R32":
        return {"next_round": "R16", "next_md": (md + 1) // 2, "slot": "home" if md % 2 == 1 else "away"}
    if round_key == "R16":
        return {"next_round": "QF", "next_md": (md + 1) // 2, "slot": "home" if md % 2 == 1 else "away"}
    if round_key == "QF":
        return {"next_round": "SF", "next_md": (md + 1) // 2, "slot": "home" if md % 2 == 1 else "away"}
    if round_key == "SF":
        # Vainqueur SF #1 → home Finale, SF #2 → away Finale
        return {"next_round": "F", "next_md": 1, "slot": "home" if md == 1 else "away"}
    return None  # Finale ou 3e place : pas de tour suivant


def _loser_slot_for(round_key: str, md: int) -> Optional[dict]:
    """Perdants : uniquement les SF alimentent le match pour la 3e place."""
    if round_key == "SF":
        return {"next_round": "3RD", "next_md": 1, "slot": "home" if md == 1 else "away"}
    return None


async def _set_team_in_slot(round_key: str, matchday: int, slot: str, team_name: str, team_code: str):
    """Met à jour le slot home/away d'un match knockout. Idempotent."""
    await db.matches.update_one(
        {"phase": "knockout", "round": round_key, "matchday": matchday},
        {"$set": {f"{slot}_team": team_name, f"{slot}_code": team_code}},
    )


async def propagate_knockout_winner(match_id: str):
    """
    Quand un match knockout passe à 'finished', propage le vainqueur (et le perdant
    de demi-finale vers le match pour la 3e place).

    Égalité au score : nécessite que payload.winner soit "home" ou "away" (tirs au but),
    sinon la propagation est sautée.
    """
    match = await db.matches.find_one({"id": match_id}, {"_id": 0})
    if not match or match.get("phase") != "knockout" or match.get("status") != "finished":
        return
    ha = match["home_score_actual"]
    aa = match["away_score_actual"]
    if ha is None or aa is None:
        return

    explicit_winner = match.get("winner_side")  # "home" | "away" | None
    if ha > aa:
        winner_side = "home"
    elif aa > ha:
        winner_side = "away"
    else:
        if explicit_winner not in ("home", "away"):
            logger.info(f"Égalité sans 'winner' explicite sur {match_id} - propagation sautée")
            return
        winner_side = explicit_winner

    loser_side = "away" if winner_side == "home" else "home"
    winner_name = match[f"{winner_side}_team"]
    winner_code = match[f"{winner_side}_code"]
    loser_name = match[f"{loser_side}_team"]
    loser_code = match[f"{loser_side}_code"]

    round_key = match["round"]
    md = match["matchday"]

    win_target = _next_slot_for(round_key, md)
    if win_target:
        await _set_team_in_slot(
            win_target["next_round"], win_target["next_md"], win_target["slot"],
            winner_name, winner_code,
        )
        logger.info(
            f"Bracket: {round_key}#{md} vainqueur {winner_name} → "
            f"{win_target['next_round']}#{win_target['next_md']} ({win_target['slot']})"
        )

    lose_target = _loser_slot_for(round_key, md)
    if lose_target:
        await _set_team_in_slot(
            lose_target["next_round"], lose_target["next_md"], lose_target["slot"],
            loser_name, loser_code,
        )
        logger.info(
            f"Bracket: {round_key}#{md} perdant {loser_name} → "
            f"{lose_target['next_round']}#{lose_target['next_md']} ({lose_target['slot']})"
        )


# ------------------------------------------------------------------
# Routes Auth
# ------------------------------------------------------------------
@api.post("/auth/register", response_model=AuthOut)
async def register(payload: RegisterIn):
    pseudo = payload.pseudo.strip()
    if await db.users.find_one({"pseudo": pseudo}):
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà pris")

    user = {
        "id": str(uuid.uuid4()),
        "pseudo": pseudo,
        "pin_hash": hash_password(payload.pin),
        "total_points": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    token = create_access_token(user["id"], pseudo)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "pseudo": user["pseudo"],
            "total_points": 0,
            "created_at": user["created_at"],
        },
    }


@api.post("/auth/login", response_model=AuthOut)
async def login(payload: LoginIn):
    pseudo = payload.pseudo.strip()
    user = await db.users.find_one({"pseudo": pseudo})
    if not user or not verify_password(payload.pin, user["pin_hash"]):
        raise HTTPException(status_code=401, detail="Pseudo ou code PIN invalide")
    token = create_access_token(user["id"], pseudo)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "pseudo": user["pseudo"],
            "total_points": user.get("total_points", 0),
            "created_at": user["created_at"],
        },
    }


@api.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "pseudo": user["pseudo"],
        "total_points": user.get("total_points", 0),
        "created_at": user["created_at"],
    }


# ------------------------------------------------------------------
# Routes Matches
# ------------------------------------------------------------------
@api.get("/matches", response_model=List[MatchOut])
async def list_matches(date: Optional[str] = None, group: Optional[str] = None):
    query = {}
    if date:
        query["display_date"] = date
    if group:
        query["group"] = group
    matches = await db.matches.find(query, {"_id": 0}).sort("kickoff_utc", 1).to_list(500)
    return matches


@api.get("/matches/dates")
async def list_match_dates():
    """Retourne la liste de toutes les dates distinctes (triées)."""
    dates = await db.matches.distinct("display_date")
    return sorted(dates)


@api.get("/matches/grouped")
async def list_matches_grouped(date: Optional[str] = None):
    """Retourne les matchs groupés. En phase de groupes : (group, matchday). En éliminatoire : par round."""
    query = {}
    if date:
        query["display_date"] = date
    matches = await db.matches.find(query, {"_id": 0}).sort("kickoff_utc", 1).to_list(500)

    grouped = {}
    for m in matches:
        phase = m.get("phase", "group")
        if phase == "knockout":
            key = f"KO-{m['round']}"
            grouped.setdefault(key, {
                "phase": "knockout",
                "round": m["round"],
                "round_label": m.get("round_label", m["round"]),
                "group": m["round"],
                "matchday": 0,
                "matches": [],
            })
        else:
            key = f"G-{m['group']}-{m['matchday']}"
            grouped.setdefault(key, {
                "phase": "group",
                "group": m["group"],
                "matchday": m["matchday"],
                "matches": [],
            })
        grouped[key]["matches"].append(m)

    # Tri : groupes d'abord, puis éliminatoire dans l'ordre des rounds
    round_order = {"R32": 1, "R16": 2, "QF": 3, "SF": 4, "3RD": 5, "F": 6}
    return sorted(
        grouped.values(),
        key=lambda x: (
            x["phase"] == "knockout",
            round_order.get(x.get("round", ""), 99) if x["phase"] == "knockout" else 0,
            x.get("group", ""),
            x.get("matchday", 0),
        ),
    )


async def _compute_group_standings(group: str) -> list[dict]:
    """Calcul interne du classement d'un groupe (réutilisé par la route et la sortie auto vers R32)."""
    matches = await db.matches.find(
        {"group": group.upper(), "phase": "group"}, {"_id": 0}
    ).to_list(50)
    standings = {}
    for m in matches:
        for side in ("home", "away"):
            team = m[f"{side}_team"]
            code = m[f"{side}_code"]
            standings.setdefault(team, {
                "team": team, "code": code,
                "pts": 0, "j": 0, "g": 0, "n": 0, "p": 0, "bp": 0, "bc": 0,
            })
        if m["status"] in ("live", "finished") and m["home_score_actual"] is not None:
            hs, as_ = m["home_score_actual"], m["away_score_actual"]
            standings[m["home_team"]]["j"] += 1
            standings[m["away_team"]]["j"] += 1
            standings[m["home_team"]]["bp"] += hs
            standings[m["home_team"]]["bc"] += as_
            standings[m["away_team"]]["bp"] += as_
            standings[m["away_team"]]["bc"] += hs
            if hs > as_:
                standings[m["home_team"]]["pts"] += 3
                standings[m["home_team"]]["g"] += 1
                standings[m["away_team"]]["p"] += 1
            elif hs < as_:
                standings[m["away_team"]]["pts"] += 3
                standings[m["away_team"]]["g"] += 1
                standings[m["home_team"]]["p"] += 1
            else:
                standings[m["home_team"]]["pts"] += 1
                standings[m["away_team"]]["pts"] += 1
                standings[m["home_team"]]["n"] += 1
                standings[m["away_team"]]["n"] += 1
    rows = list(standings.values())
    for r in rows:
        r["diff"] = r["bp"] - r["bc"]
    rows.sort(key=lambda x: (-x["pts"], -x["diff"], -x["bp"]))
    return rows


@api.get("/standings/{group}")
async def group_standings(group: str):
    """Classement en direct d'un groupe (4 équipes)."""
    return await _compute_group_standings(group)


# ------------------------------------------------------------------
# Routes Predictions
# ------------------------------------------------------------------
@api.post("/predictions", response_model=PredictionOut)
async def upsert_prediction(payload: PredictionIn, user: dict = Depends(get_current_user)):
    match = await db.matches.find_one({"id": payload.match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match["status"] != "scheduled":
        raise HTTPException(status_code=400, detail="Les pronostics sont clos pour ce match")

    existing = await db.predictions.find_one(
        {"user_id": user["id"], "match_id": payload.match_id}, {"_id": 0}
    )
    if existing:
        await db.predictions.update_one(
            {"id": existing["id"]},
            {"$set": {
                "home_score_predicted": payload.home_score_predicted,
                "away_score_predicted": payload.away_score_predicted,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        existing.update({
            "home_score_predicted": payload.home_score_predicted,
            "away_score_predicted": payload.away_score_predicted,
        })
        return existing

    new_pred = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "match_id": payload.match_id,
        "home_score_predicted": payload.home_score_predicted,
        "away_score_predicted": payload.away_score_predicted,
        "points_earned": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.predictions.insert_one(new_pred)
    return new_pred


@api.get("/predictions/me", response_model=List[PredictionOut])
async def my_predictions(user: dict = Depends(get_current_user)):
    preds = await db.predictions.find({"user_id": user["id"]}, {"_id": 0}).to_list(2000)
    return preds


# ------------------------------------------------------------------
# Routes Admin (résultats des matchs)
# ------------------------------------------------------------------
def require_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Token admin invalide")
    return True


@api.post("/admin/match-result")
async def set_match_result(payload: MatchResultIn, _: bool = Depends(require_admin)):
    """Enregistre le résultat d'un match. Si status=finished, recalcule les points
    et propage le vainqueur dans le bracket si c'est un match knockout."""
    match = await db.matches.find_one({"id": payload.match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match introuvable")

    update = {
        "home_score_actual": payload.home_score_actual,
        "away_score_actual": payload.away_score_actual,
        "status": payload.status,
    }
    # Mémorise un éventuel vainqueur explicite (égalité en knockout / tirs au but)
    if payload.winner is not None:
        update["winner_side"] = payload.winner

    await db.matches.update_one({"id": payload.match_id}, {"$set": update})

    if payload.status == "finished":
        await recalculate_match_points(payload.match_id)
        if match.get("phase") == "knockout":
            await propagate_knockout_winner(payload.match_id)

    return {"ok": True, "match_id": payload.match_id, "status": payload.status}


@api.patch("/admin/match-teams")
async def set_match_teams(payload: MatchTeamsIn, _: bool = Depends(require_admin)):
    """
    Met à jour les équipes d'un match (utile pour la phase éliminatoire
    quand le bracket se remplit). Seuls les champs fournis sont modifiés.

    Body attendu :
      {
        "match_id": "...",
        "home_team": "Brésil",        // optionnel
        "home_code": "br",            // optionnel
        "away_team": "France",        // optionnel
        "away_code": "fr"             // optionnel
      }

    Note: les pronostics déjà saisis sur ce match restent valides
    (le score prédit reste lié au match_id, pas aux noms d'équipes).
    """
    match = await db.matches.find_one({"id": payload.match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match introuvable")

    update_fields = {}
    if payload.home_team is not None:
        update_fields["home_team"] = payload.home_team.strip()
    if payload.home_code is not None:
        update_fields["home_code"] = payload.home_code.strip().lower()
    if payload.away_team is not None:
        update_fields["away_team"] = payload.away_team.strip()
    if payload.away_code is not None:
        update_fields["away_code"] = payload.away_code.strip().lower()

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    await db.matches.update_one({"id": payload.match_id}, {"$set": update_fields})
    updated = await db.matches.find_one({"id": payload.match_id}, {"_id": 0})
    return {"ok": True, "match": updated}


# ------------------------------------------------------------------
# Sortie automatique de la phase de groupes → R32
# ------------------------------------------------------------------
# Matrice de mapping. Slots :
#   - ("1", "A") = vainqueur du groupe A
#   - ("2", "B") = 2e du groupe B
#   - ("3", k)   = k-ième meilleur 3e (1..8)
# Total : 12 vainqueurs + 12 deuxièmes + 8 troisièmes = 32 places
R32_MAPPING = [
    (("1", "A"), ("2", "B")),     # R32 #1
    (("1", "C"), ("2", "D")),     # R32 #2
    (("1", "E"), ("2", "F")),     # R32 #3
    (("1", "B"), ("3", 1)),       # R32 #4
    (("1", "D"), ("3", 2)),       # R32 #5
    (("1", "F"), ("3", 3)),       # R32 #6
    (("2", "A"), ("2", "C")),     # R32 #7
    (("2", "E"), ("3", 4)),       # R32 #8
    (("1", "G"), ("2", "H")),     # R32 #9
    (("1", "I"), ("2", "J")),     # R32 #10
    (("1", "K"), ("2", "L")),     # R32 #11
    (("1", "H"), ("3", 5)),       # R32 #12
    (("1", "J"), ("3", 6)),       # R32 #13
    (("1", "L"), ("3", 7)),       # R32 #14
    (("2", "G"), ("2", "I")),     # R32 #15
    (("2", "K"), ("3", 8)),       # R32 #16
]


@api.post("/admin/seed-r32-from-groups")
async def seed_r32_from_groups(_: bool = Depends(require_admin)):
    """
    Calcule automatiquement les 16 affiches du R32 à partir des résultats de phase de groupes :
      - 12 vainqueurs de groupe
      - 12 deuxièmes de groupe
      - 8 meilleurs 3es de groupe (classés sur Pts > Diff > BP)
    Puis les place dans les R32 selon une matrice fixe (R32_MAPPING).

    Pré-requis : tous les matchs de phase de groupes doivent être au statut 'finished'.
    L'endpoint est idempotent (peut être ré-exécuté pour rafraîchir).
    """
    unfinished = await db.matches.count_documents({"phase": "group", "status": {"$ne": "finished"}})
    if unfinished > 0:
        raise HTTPException(
            status_code=400,
            detail=f"{unfinished} matchs de phase de groupes ne sont pas encore terminés",
        )

    # Calcul de tous les classements
    standings_by_group = {}
    for letter in "ABCDEFGHIJKL":
        rows = await _compute_group_standings(letter)
        if len(rows) < 3:
            raise HTTPException(
                status_code=500,
                detail=f"Groupe {letter} : moins de 3 équipes trouvées",
            )
        standings_by_group[letter] = rows

    # Ranking des 12 troisièmes
    thirds = []
    for letter, rows in standings_by_group.items():
        third = dict(rows[2])
        third["from_group"] = letter
        thirds.append(third)
    thirds.sort(key=lambda x: (-x["pts"], -x["diff"], -x["bp"]))
    top_8_thirds = thirds[:8]

    def resolve_slot(slot):
        kind, ref = slot
        if kind == "3":
            t = top_8_thirds[ref - 1]
            return t["team"], t["code"]
        # "1" ou "2" + lettre de groupe
        rank_idx = int(kind) - 1
        row = standings_by_group[ref][rank_idx]
        return row["team"], row["code"]

    summary = []
    for i, (h_slot, a_slot) in enumerate(R32_MAPPING):
        md = i + 1
        h_name, h_code = resolve_slot(h_slot)
        a_name, a_code = resolve_slot(a_slot)
        await db.matches.update_one(
            {"phase": "knockout", "round": "R32", "matchday": md},
            {"$set": {
                "home_team": h_name, "home_code": h_code,
                "away_team": a_name, "away_code": a_code,
                # Reset scores/status car l'identité des équipes change
                "home_score_actual": None,
                "away_score_actual": None,
                "status": "scheduled",
            }, "$unset": {"winner_side": ""}},
        )
        summary.append({
            "matchday": md,
            "home": h_name,
            "home_slot": f"{h_slot[0]}{h_slot[1]}",
            "away": a_name,
            "away_slot": f"{a_slot[0]}{a_slot[1]}",
        })

    return {
        "ok": True,
        "matches_seeded": 16,
        "best_thirds": [
            {"rank": i + 1, "group": t["from_group"], "team": t["team"], "pts": t["pts"], "diff": t["diff"]}
            for i, t in enumerate(top_8_thirds)
        ],
        "matches": summary,
    }


# ------------------------------------------------------------------
# Routes Leaderboard / Dashboard
# ------------------------------------------------------------------
@api.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard(limit: int = 100):
    users = await db.users.find({}, {"_id": 0, "pseudo": 1, "total_points": 1}) \
        .sort("total_points", -1).to_list(limit)
    return [
        {"rank": i + 1, "pseudo": u["pseudo"], "total_points": u.get("total_points", 0)}
        for i, u in enumerate(users)
    ]


@api.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "id": 1, "total_points": 1}) \
        .sort("total_points", -1).to_list(10000)
    rank = next((i + 1 for i, u in enumerate(users) if u["id"] == user["id"]), None)
    total_users = len(users)
    preds_count = await db.predictions.count_documents({"user_id": user["id"]})
    return {
        "pseudo": user["pseudo"],
        "total_points": user.get("total_points", 0),
        "rank": rank,
        "total_users": total_users,
        "predictions_count": preds_count,
    }


# ------------------------------------------------------------------
# Routes Ligues privées
# ------------------------------------------------------------------
import secrets as _secrets


def _generate_invite_code() -> str:
    """Code d'invitation de 6 caractères alphanumériques (lisibles)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans I/O/0/1 pour lisibilité
    return "".join(_secrets.choice(alphabet) for _ in range(6))


class LeagueCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=40)


class LeagueJoinIn(BaseModel):
    invite_code: str = Field(min_length=4, max_length=10)


class LeagueOut(BaseModel):
    id: str
    name: str
    invite_code: str
    owner_id: str
    owner_pseudo: str
    member_ids: List[str]
    member_count: int
    created_at: str


class LeagueMemberRow(BaseModel):
    rank: int
    user_id: str
    pseudo: str
    total_points: int


@api.post("/leagues", response_model=LeagueOut)
async def create_league(payload: LeagueCreateIn, user: dict = Depends(get_current_user)):
    # Code unique (très peu de chances de collision sur 32^6)
    for _ in range(5):
        code = _generate_invite_code()
        if not await db.leagues.find_one({"invite_code": code}):
            break
    league = {
        "id": str(uuid.uuid4()),
        "name": payload.name.strip(),
        "invite_code": code,
        "owner_id": user["id"],
        "owner_pseudo": user["pseudo"],
        "member_ids": [user["id"]],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.leagues.insert_one(league)
    league.pop("_id", None)
    return {**league, "member_count": 1}


@api.post("/leagues/join", response_model=LeagueOut)
async def join_league(payload: LeagueJoinIn, user: dict = Depends(get_current_user)):
    code = payload.invite_code.strip().upper()
    league = await db.leagues.find_one({"invite_code": code}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="Code d'invitation introuvable")
    if user["id"] not in league["member_ids"]:
        await db.leagues.update_one(
            {"id": league["id"]},
            {"$addToSet": {"member_ids": user["id"]}},
        )
        league["member_ids"].append(user["id"])
    return {**league, "member_count": len(league["member_ids"])}


@api.get("/leagues/me", response_model=List[LeagueOut])
async def my_leagues(user: dict = Depends(get_current_user)):
    leagues = await db.leagues.find({"member_ids": user["id"]}, {"_id": 0}) \
        .sort("created_at", -1).to_list(200)
    return [{**lg, "member_count": len(lg["member_ids"])} for lg in leagues]


@api.get("/leagues/{league_id}", response_model=LeagueOut)
async def get_league(league_id: str, user: dict = Depends(get_current_user)):
    lg = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable")
    if user["id"] not in lg["member_ids"]:
        raise HTTPException(status_code=403, detail="Tu n'es pas membre de cette ligue")
    return {**lg, "member_count": len(lg["member_ids"])}


@api.get("/leagues/{league_id}/leaderboard", response_model=List[LeagueMemberRow])
async def league_leaderboard(league_id: str, user: dict = Depends(get_current_user)):
    lg = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable")
    if user["id"] not in lg["member_ids"]:
        raise HTTPException(status_code=403, detail="Tu n'es pas membre de cette ligue")
    members = await db.users.find(
        {"id": {"$in": lg["member_ids"]}},
        {"_id": 0, "id": 1, "pseudo": 1, "total_points": 1},
    ).to_list(500)
    members.sort(key=lambda u: -u.get("total_points", 0))
    return [
        {
            "rank": i + 1,
            "user_id": u["id"],
            "pseudo": u["pseudo"],
            "total_points": u.get("total_points", 0),
        }
        for i, u in enumerate(members)
    ]


@api.delete("/leagues/{league_id}/leave")
async def leave_league(league_id: str, user: dict = Depends(get_current_user)):
    lg = await db.leagues.find_one({"id": league_id})
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable")
    if lg["owner_id"] == user["id"]:
        # Owner quitte = supprime la ligue
        await db.leagues.delete_one({"id": league_id})
        return {"ok": True, "deleted": True}
    await db.leagues.update_one(
        {"id": league_id},
        {"$pull": {"member_ids": user["id"]}},
    )
    return {"ok": True, "deleted": False}


# ------------------------------------------------------------------
# Startup : seed des matches + indexes
# ------------------------------------------------------------------
@app.on_event("startup")
async def startup_seed():
    await db.users.create_index("pseudo", unique=True)
    await db.matches.create_index("display_date")
    await db.matches.create_index("group")
    await db.predictions.create_index([("user_id", 1), ("match_id", 1)], unique=True)
    await db.leagues.create_index("invite_code", unique=True)
    await db.leagues.create_index("member_ids")

    # Phase de groupes
    group_count = await db.matches.count_documents({"phase": "group"})
    legacy_count = await db.matches.count_documents({"phase": {"$exists": False}})
    if group_count == 0 and legacy_count == 0:
        fixtures = build_group_stage_matches()
        docs = [{**m, "id": str(uuid.uuid4())} for m in fixtures]
        if docs:
            await db.matches.insert_many(docs)
        logger.info(f"Seeded {len(docs)} group-stage matches")
    elif legacy_count > 0:
        # Migration : matchs préexistants sans phase
        await db.matches.update_many({"phase": {"$exists": False}}, {"$set": {"phase": "group", "round": None}})
        logger.info(f"Migrated {legacy_count} legacy matches with phase=group")

    # Phase à élimination directe
    ko_count = await db.matches.count_documents({"phase": "knockout"})
    if ko_count == 0:
        ko_fixtures = build_knockout_matches()
        docs = [{**m, "id": str(uuid.uuid4())} for m in ko_fixtures]
        if docs:
            await db.matches.insert_many(docs)
        logger.info(f"Seeded {len(docs)} knockout matches")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------
@api.get("/")
async def root():
    return {"message": "WC2026 Pronostics API", "status": "ok"}


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
