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

from fixtures import build_group_stage_matches

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


class MatchResultIn(BaseModel):
    match_id: str
    home_score_actual: int = Field(ge=0, le=99)
    away_score_actual: int = Field(ge=0, le=99)
    status: Literal["live", "finished"] = "finished"


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
    """Retourne les matchs groupés par (group, matchday) pour la date demandée."""
    query = {}
    if date:
        query["display_date"] = date
    matches = await db.matches.find(query, {"_id": 0}).sort("kickoff_utc", 1).to_list(500)

    grouped = {}
    for m in matches:
        key = f"{m['group']}-{m['matchday']}"
        grouped.setdefault(key, {
            "group": m["group"],
            "matchday": m["matchday"],
            "matches": [],
        })
        grouped[key]["matches"].append(m)

    # Tri par lettre de groupe puis par journée
    return sorted(grouped.values(), key=lambda x: (x["group"], x["matchday"]))


@api.get("/standings/{group}")
async def group_standings(group: str):
    """Calcule le classement en direct d'un groupe (4 équipes)."""
    matches = await db.matches.find({"group": group.upper()}, {"_id": 0}).to_list(50)
    standings = {}

    for m in matches:
        for side, opp_side in [("home", "away"), ("away", "home")]:
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
    """Enregistre le résultat d'un match. Si status=finished, recalcule les points."""
    match = await db.matches.find_one({"id": payload.match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match introuvable")
    await db.matches.update_one(
        {"id": payload.match_id},
        {"$set": {
            "home_score_actual": payload.home_score_actual,
            "away_score_actual": payload.away_score_actual,
            "status": payload.status,
        }},
    )
    if payload.status == "finished":
        await recalculate_match_points(payload.match_id)
    return {"ok": True, "match_id": payload.match_id, "status": payload.status}


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
# Startup : seed des matches + indexes
# ------------------------------------------------------------------
@app.on_event("startup")
async def startup_seed():
    await db.users.create_index("pseudo", unique=True)
    await db.matches.create_index("display_date")
    await db.matches.create_index("group")
    await db.predictions.create_index([("user_id", 1), ("match_id", 1)], unique=True)

    count = await db.matches.count_documents({})
    if count == 0:
        fixtures = build_group_stage_matches()
        docs = []
        for m in fixtures:
            m_copy = dict(m)
            m_copy["id"] = str(uuid.uuid4())
            docs.append(m_copy)
        if docs:
            await db.matches.insert_many(docs)
        logger.info(f"Seeded {len(docs)} matches Coupe du Monde 2026")
    else:
        logger.info(f"{count} matches already in DB - skipping seed")


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
