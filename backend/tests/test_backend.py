"""Backend tests for WC2026 Pronostics API."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://predict-2026-world.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"
ADMIN_TOKEN = "wc2026-admin-secret-token"

# Unique user per run to avoid duplicate conflicts
RUN_TAG = uuid.uuid4().hex[:8]
TEST_EMAIL = f"test_{RUN_TAG}@wc2026.fr"
TEST_PSEUDO = f"TestUser_{RUN_TAG}"
TEST_PASS = "test1234"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth(session):
    r = session.post(f"{API}/auth/register", json={
        "email": TEST_EMAIL, "pseudo": TEST_PSEUDO, "password": TEST_PASS,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "token" in data and "user" in data
    return data


# --- Auth ---
class TestAuth:
    def test_register_duplicate_email(self, session, auth):
        r = session.post(f"{API}/auth/register", json={
            "email": TEST_EMAIL, "pseudo": f"Other_{RUN_TAG}", "password": TEST_PASS,
        })
        assert r.status_code == 400

    def test_register_duplicate_pseudo(self, session, auth):
        r = session.post(f"{API}/auth/register", json={
            "email": f"other_{RUN_TAG}@wc.fr", "pseudo": TEST_PSEUDO, "password": TEST_PASS,
        })
        assert r.status_code == 400

    def test_login_ok(self, session, auth):
        r = session.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS})
        assert r.status_code == 200
        assert r.json()["user"]["pseudo"] == TEST_PSEUDO

    def test_login_bad(self, session, auth):
        r = session.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": "wrong"})
        assert r.status_code == 401

    def test_me(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/auth/me", headers=h)
        assert r.status_code == 200
        assert r.json()["email"] == TEST_EMAIL


# --- Matches ---
class TestMatches:
    def test_dates(self, session):
        r = session.get(f"{API}/matches/dates")
        assert r.status_code == 200
        dates = r.json()
        assert isinstance(dates, list)
        assert len(dates) == 15, f"Expected 15 dates, got {len(dates)}"
        assert dates == sorted(dates)

    def test_grouped_qatar_suisse(self, session):
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-12"})
        assert r.status_code == 200
        groups = r.json()
        all_matches = [m for g in groups for m in g["matches"]]
        target = [m for m in all_matches if {m["home_team"], m["away_team"]} == {"Qatar", "Suisse"}]
        assert target, "Qatar vs Suisse not found on 2026-06-12"
        m = target[0]
        assert m["kickoff_hour_paris"] == 21, f"Expected 21h, got {m['kickoff_hour_paris']}"
        assert "beIN Sports 1" in m["broadcast_channels"]
        assert "M6" in m["broadcast_channels"]

    def test_grouped_bresil_maroc_haiti_ecosse(self, session):
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-14"})
        assert r.status_code == 200
        all_matches = [m for g in r.json() for m in g["matches"]]
        bm = [m for m in all_matches if {m["home_team"], m["away_team"]} == {"Brésil", "Maroc"}]
        he = [m for m in all_matches if {m["home_team"], m["away_team"]} == {"Haïti", "Écosse"}]
        assert bm, "Brésil vs Maroc missing"
        assert he, "Haïti vs Écosse missing"
        assert bm[0]["kickoff_hour_paris"] == 0
        assert "beIN Sports 1" in bm[0]["broadcast_channels"] and "M6" in bm[0]["broadcast_channels"]
        assert he[0]["kickoff_hour_paris"] == 3
        assert "beIN Sports 1" in he[0]["broadcast_channels"]


# --- Standings ---
class TestStandings:
    def test_group_a(self, session):
        r = session.get(f"{API}/standings/A")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 4
        assert all(row["pts"] == 0 for row in rows)


# --- Predictions + Admin + Points calculator ---
class TestPredictionsAndPoints:
    def _get_scheduled_match(self, session):
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-12"})
        for g in r.json():
            for m in g["matches"]:
                if m["status"] == "scheduled":
                    return m
        return None

    def test_create_and_update_prediction(self, session, auth):
        m = self._get_scheduled_match(session)
        assert m
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.post(f"{API}/predictions", headers=h, json={
            "match_id": m["id"], "home_score_predicted": 1, "away_score_predicted": 0,
        })
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        # update (upsert by user+match)
        r2 = session.post(f"{API}/predictions", headers=h, json={
            "match_id": m["id"], "home_score_predicted": 2, "away_score_predicted": 1,
        })
        assert r2.status_code == 200
        assert r2.json()["home_score_predicted"] == 2
        assert r2.json()["id"] == pid  # same prediction

        # /predictions/me returns only user preds
        rm = session.get(f"{API}/predictions/me", headers=h)
        assert rm.status_code == 200
        ids = [p["id"] for p in rm.json()]
        assert pid in ids

    def test_admin_bad_token(self, session):
        r = session.post(f"{API}/admin/match-result",
                         headers={"X-Admin-Token": "wrong"},
                         json={"match_id": "x", "home_score_actual": 0, "away_score_actual": 0, "status": "finished"})
        assert r.status_code == 403

    def test_full_points_flow(self, session):
        # Create dedicated user
        email = f"pts_{uuid.uuid4().hex[:6]}@wc.fr"
        pseudo = f"Pts_{uuid.uuid4().hex[:6]}"
        reg = session.post(f"{API}/auth/register", json={"email": email, "pseudo": pseudo, "password": "test1234"})
        assert reg.status_code == 200
        token = reg.json()["token"]
        h = {"Authorization": f"Bearer {token}"}

        # Pick a scheduled match
        m = self._get_scheduled_match(session)
        assert m

        # Predict 2-1
        pr = session.post(f"{API}/predictions", headers=h,
                          json={"match_id": m["id"], "home_score_predicted": 2, "away_score_predicted": 1})
        assert pr.status_code == 200

        # Set result to 2-1 (exact score => 1 + 1 + 3 = 5 pts)
        ar = session.post(f"{API}/admin/match-result",
                          headers={"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"},
                          json={"match_id": m["id"], "home_score_actual": 2, "away_score_actual": 1, "status": "finished"})
        assert ar.status_code == 200, ar.text

        # Verify points via dashboard
        d = session.get(f"{API}/dashboard", headers=h)
        assert d.status_code == 200
        assert d.json()["total_points"] == 5, f"Expected 5, got {d.json()}"

        # Prediction closed now
        closed = session.post(f"{API}/predictions", headers=h,
                              json={"match_id": m["id"], "home_score_predicted": 0, "away_score_predicted": 0})
        assert closed.status_code == 400


# --- Leaderboard / Dashboard ---
class TestLeaderboardDashboard:
    def test_leaderboard(self, session):
        r = session.get(f"{API}/leaderboard")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if len(data) >= 2:
            assert data[0]["rank"] == 1
            assert data[0]["total_points"] >= data[1]["total_points"]

    def test_dashboard(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/dashboard", headers=h)
        assert r.status_code == 200
        d = r.json()
        for k in ("pseudo", "total_points", "rank", "total_users", "predictions_count"):
            assert k in d
