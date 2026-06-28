"""Backend tests for WC2026 Pronostics API.

Covers:
- Auth (pseudo + PIN)
- Matches: dates (group + knockout), grouped (group + KO)
- Predictions on group and knockout matches
- Standings, leaderboard, dashboard
- Private leagues : create / join / me / get / leaderboard / leave
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"
ADMIN_TOKEN = "wc2026-admin-secret-token"

RUN_TAG = uuid.uuid4().hex[:6].upper()
TEST_PSEUDO = f"TST{RUN_TAG}"
TEST_PIN = "1234"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth(session):
    """Register a fresh user for the test session."""
    r = session.post(f"{API}/auth/register", json={"pseudo": TEST_PSEUDO, "pin": TEST_PIN})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "token" in data and "user" in data
    assert data["user"]["pseudo"] == TEST_PSEUDO
    return data


@pytest.fixture(scope="session")
def auth2(session):
    """Second user for multi-user league tests."""
    pseudo = f"TST{uuid.uuid4().hex[:6].upper()}"
    r = session.post(f"{API}/auth/register", json={"pseudo": pseudo, "pin": "5678"})
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------- Auth ----------------------
class TestAuth:
    def test_register_duplicate_pseudo(self, session, auth):
        r = session.post(f"{API}/auth/register", json={"pseudo": TEST_PSEUDO, "pin": "9999"})
        assert r.status_code == 400

    def test_login_ok(self, session, auth):
        r = session.post(f"{API}/auth/login", json={"pseudo": TEST_PSEUDO, "pin": TEST_PIN})
        assert r.status_code == 200
        assert r.json()["user"]["pseudo"] == TEST_PSEUDO

    def test_login_bad_pin(self, session, auth):
        r = session.post(f"{API}/auth/login", json={"pseudo": TEST_PSEUDO, "pin": "0000"})
        assert r.status_code == 401

    def test_me(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/auth/me", headers=h)
        assert r.status_code == 200
        assert r.json()["pseudo"] == TEST_PSEUDO

    def test_pin_format(self, session):
        r = session.post(f"{API}/auth/register", json={"pseudo": f"X{RUN_TAG}", "pin": "abc"})
        assert r.status_code == 422


# ---------------------- Matches ----------------------
class TestMatches:
    def test_dates_includes_final(self, session):
        r = session.get(f"{API}/matches/dates")
        assert r.status_code == 200
        dates = r.json()
        assert isinstance(dates, list)
        assert "2026-07-19" in dates, "Final date 2026-07-19 missing"
        assert dates == sorted(dates)
        # 48 group matches across 12+ dates plus 32 KO matches; expect ~30 dates
        assert len(dates) >= 25, f"Expected >=25 dates, got {len(dates)}"

    def test_grouped_final(self, session):
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-07-19"})
        assert r.status_code == 200
        sections = r.json()
        ko = [s for s in sections if s.get("phase") == "knockout"]
        assert ko, "No knockout section on 2026-07-19"
        final = [s for s in ko if s.get("round") == "F"]
        assert final, "Final section missing"
        s = final[0]
        assert s["round_label"] == "Finale"
        assert s["matches"], "Final has no match"
        m = s["matches"][0]
        assert m["phase"] == "knockout"
        assert m["round"] == "F"
        assert m["home_team"] == "À déterminer"
        assert m["home_code"] == ""
        assert m["away_team"] == "À déterminer"
        assert m["away_code"] == ""

    def test_grouped_r32(self, session):
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-27"})
        assert r.status_code == 200
        sections = r.json()
        ko = [s for s in sections if s.get("phase") == "knockout" and s.get("round") == "R32"]
        assert ko, "No R32 section on 2026-06-27"
        assert ko[0]["matches"], "R32 section has no match"

    def test_grouped_group_phase_regression(self, session):
        """Regression: group phase still returns sections with group + matchday."""
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-12"})
        assert r.status_code == 200
        sections = r.json()
        groups = [s for s in sections if s.get("phase") == "group"]
        assert groups, "Expected at least one group section on opening day"
        s = groups[0]
        assert "group" in s and "matchday" in s
        assert s["matches"]


# ---------------------- Predictions ----------------------
def _find_scheduled_match(session, date=None, phase=None):
    params = {"date": date} if date else {}
    r = session.get(f"{API}/matches/grouped", params=params)
    for s in r.json():
        if phase and s.get("phase") != phase:
            continue
        for m in s["matches"]:
            if m["status"] == "scheduled":
                return m
    return None


class TestPredictions:
    def test_create_prediction_group(self, session, auth):
        m = _find_scheduled_match(session, date="2026-06-12")
        assert m, "No scheduled group match found"
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.post(f"{API}/predictions", headers=h, json={
            "match_id": m["id"], "home_score_predicted": 1, "away_score_predicted": 0,
        })
        assert r.status_code == 200, r.text
        assert r.json()["home_score_predicted"] == 1

    def test_create_prediction_knockout(self, session, auth):
        # find any KO match (e.g. R32)
        r = session.get(f"{API}/matches/grouped", params={"date": "2026-06-27"})
        ko_match = None
        for s in r.json():
            if s.get("phase") == "knockout":
                for m in s["matches"]:
                    if m["status"] == "scheduled":
                        ko_match = m
                        break
            if ko_match:
                break
        assert ko_match, "No KO scheduled match found"
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.post(f"{API}/predictions", headers=h, json={
            "match_id": ko_match["id"], "home_score_predicted": 2, "away_score_predicted": 2,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["home_score_predicted"] == 2 and body["away_score_predicted"] == 2

    def test_predictions_me(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/predictions/me", headers=h)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------- Leaderboard / Dashboard ----------------------
class TestLeaderboardDashboard:
    def test_leaderboard(self, session):
        r = session.get(f"{API}/leaderboard")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_dashboard(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/dashboard", headers=h)
        assert r.status_code == 200
        for k in ("pseudo", "total_points", "rank", "total_users", "predictions_count"):
            assert k in r.json()


# ---------------------- Leagues ----------------------
class TestLeagues:
    league_id = None
    invite_code = None

    def test_create_league(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.post(f"{API}/leagues", headers=h, json={"name": f"Lg_{RUN_TAG}"})
        assert r.status_code == 200, r.text
        lg = r.json()
        assert lg["name"] == f"Lg_{RUN_TAG}"
        assert len(lg["invite_code"]) == 6
        assert lg["invite_code"].isalnum() and lg["invite_code"].isupper()
        assert lg["owner_pseudo"] == TEST_PSEUDO
        assert lg["member_count"] == 1
        TestLeagues.league_id = lg["id"]
        TestLeagues.invite_code = lg["invite_code"]

    def test_create_league_unauth(self, session):
        r = session.post(f"{API}/leagues", json={"name": "NoAuth"})
        assert r.status_code == 401

    def test_join_league_invalid_code(self, session, auth2):
        h = {"Authorization": f"Bearer {auth2['token']}"}
        r = session.post(f"{API}/leagues/join", headers=h, json={"invite_code": "ZZZZZZ"})
        assert r.status_code == 404

    def test_join_league_ok(self, session, auth2):
        assert TestLeagues.invite_code
        h = {"Authorization": f"Bearer {auth2['token']}"}
        r = session.post(f"{API}/leagues/join", headers=h,
                         json={"invite_code": TestLeagues.invite_code})
        assert r.status_code == 200, r.text
        assert r.json()["member_count"] == 2

    def test_join_league_idempotent(self, session, auth2):
        h = {"Authorization": f"Bearer {auth2['token']}"}
        r = session.post(f"{API}/leagues/join", headers=h,
                         json={"invite_code": TestLeagues.invite_code})
        assert r.status_code == 200
        assert r.json()["member_count"] == 2  # not 3

    def test_my_leagues(self, session, auth, auth2):
        h2 = {"Authorization": f"Bearer {auth2['token']}"}
        r = session.get(f"{API}/leagues/me", headers=h2)
        assert r.status_code == 200
        ids = [lg["id"] for lg in r.json()]
        assert TestLeagues.league_id in ids

    def test_get_league_member(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/leagues/{TestLeagues.league_id}", headers=h)
        assert r.status_code == 200
        assert r.json()["id"] == TestLeagues.league_id

    def test_get_league_forbidden(self, session):
        # third unrelated user
        pseudo = f"OUT{uuid.uuid4().hex[:6].upper()}"
        reg = session.post(f"{API}/auth/register", json={"pseudo": pseudo, "pin": "9999"})
        assert reg.status_code == 200
        token = reg.json()["token"]
        h = {"Authorization": f"Bearer {token}"}
        r = session.get(f"{API}/leagues/{TestLeagues.league_id}", headers=h)
        assert r.status_code == 403

    def test_league_leaderboard(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.get(f"{API}/leagues/{TestLeagues.league_id}/leaderboard", headers=h)
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 2
        assert rows[0]["rank"] == 1
        assert rows[0]["total_points"] >= rows[1]["total_points"]

    def test_leave_member(self, session, auth2):
        h = {"Authorization": f"Bearer {auth2['token']}"}
        r = session.delete(f"{API}/leagues/{TestLeagues.league_id}/leave", headers=h)
        assert r.status_code == 200
        assert r.json()["deleted"] is False
        # Confirm member removed
        r2 = session.get(f"{API}/leagues/{TestLeagues.league_id}/leaderboard",
                         headers={"Authorization": f"Bearer {auth2['token']}"})
        assert r2.status_code == 403

    def test_leave_owner_deletes(self, session, auth):
        h = {"Authorization": f"Bearer {auth['token']}"}
        r = session.delete(f"{API}/leagues/{TestLeagues.league_id}/leave", headers=h)
        assert r.status_code == 200
        assert r.json()["deleted"] is True
        # Now league should not exist
        r2 = session.get(f"{API}/leagues/{TestLeagues.league_id}", headers=h)
        assert r2.status_code == 404
