from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.main import create_app
from tests.conftest import ADMIN_EMAIL, make_container, sign_in
from tests.fakes import InMemoryStore

PLAN = {"symbol": "INFY", "category": "50D", "start_date": "2026-10-30", "target_pct": 10}


@pytest.fixture
def app_store(seeded_store: InMemoryStore) -> InMemoryStore:
    """A copy of the seeded data with fresh, empty account tables."""
    store = InMemoryStore()
    store.markets, store.stocks, store.candles = (
        seeded_store.markets,
        seeded_store.stocks,
        seeded_store.candles,
    )
    store.predictions = seeded_store.predictions
    return store


def new_client(store: InMemoryStore) -> TestClient:
    return TestClient(create_app(make_container(store)))


@pytest.fixture
def admin(app_store: InMemoryStore) -> Iterator[TestClient]:
    with new_client(app_store) as client:
        sign_in(client)
        yield client


def invite(admin: TestClient, **body: object) -> str:
    response = admin.post("/api/admin/invites", json=body)
    assert response.status_code == 201, response.text
    code: str = response.json()["code"]
    return code


def test_everything_needs_a_session(anonymous_client: TestClient) -> None:
    for path in ("/api/stocks", "/api/trade-plans", "/api/screener", "/api/watchlist"):
        assert anonymous_client.get(path).status_code == 401, path
    assert anonymous_client.get("/api/health").status_code == 200
    options = anonymous_client.get("/api/auth/options").json()
    assert options == {"providers": [], "dev_login": True}


def test_session_cookie_is_http_only_and_lax(anonymous_client: TestClient) -> None:
    response = anonymous_client.post("/api/auth/dev-login", json={"email": ADMIN_EMAIL})
    cookie = response.headers["set-cookie"].lower()

    assert "httponly" in cookie and "samesite=lax" in cookie and "max-age=604800" in cookie
    assert anonymous_client.get("/api/auth/me").json()["role"] == "admin"
    assert anonymous_client.post("/api/auth/logout").status_code == 204
    assert anonymous_client.get("/api/auth/me").status_code == 401


def test_sign_up_needs_a_valid_invite(app_store: InMemoryStore, admin: TestClient) -> None:
    with new_client(app_store) as stranger:
        refused = stranger.post("/api/auth/dev-login", json={"email": "new@x.io"})
        assert refused.status_code == 401
        assert "invite code" in refused.json()["detail"]
        wrong = stranger.post(
            "/api/auth/dev-login", json={"email": "new@x.io", "invite_code": "SA-NOPE-NOPE"}
        )
        assert "does not exist" in wrong.json()["detail"]

    code = invite(admin)
    with new_client(app_store) as friend:
        sign_in(friend, "friend@x.io", code.lower())  # pasted in lower case: accepted
        assert friend.get("/api/auth/me").json()["role"] == "user"
        assert friend.get("/api/admin/users").status_code == 403
        assert friend.get("/api/admin/providers").status_code == 403
    with new_client(app_store) as second:
        reused = second.post(
            "/api/auth/dev-login", json={"email": "second@x.io", "invite_code": code}
        )
        assert "already been used" in reused.json()["detail"]

    revoked = invite(admin, max_uses=5)
    invite_id = next(
        i["id"] for i in admin.get("/api/admin/invites").json() if i["code"] == revoked
    )
    assert admin.delete(f"/api/admin/invites/{invite_id}").status_code == 204
    with new_client(app_store) as late:
        response = late.post(
            "/api/auth/dev-login", json={"email": "late@x.io", "invite_code": revoked}
        )
        assert "revoked" in response.json()["detail"]
    assert len(app_store.users) == 2  # admin + friend only


def test_users_only_see_their_own_plans(app_store: InMemoryStore, admin: TestClient) -> None:
    mine = admin.post("/api/trade-plans", json=PLAN).json()
    code = invite(admin)
    with new_client(app_store) as other:
        sign_in(other, "other@x.io", code)
        assert other.get("/api/trade-plans").json() == []
        assert other.get(f"/api/trade-plans/{mine['id']}").status_code == 404
        close = {"exit_date": "2026-12-21", "exit_price": 1000}
        assert other.post(f"/api/trade-plans/{mine['id']}/close", json=close).status_code == 404
        theirs = other.post("/api/trade-plans", json=PLAN).json()
        settings = {
            "paper_capital": 50000,
            "risk_pct": 2,
            "success_tolerance_pp": 1,
            "default_stop_pct": -5,
        }
        assert other.put("/api/settings/journal", json=settings).status_code == 200
    assert [p["id"] for p in admin.get("/api/trade-plans").json()] == [mine["id"]]
    assert theirs["id"] != mine["id"]
    assert admin.get("/api/settings/journal").json()["paper_capital"] == 1000000


def test_first_admin_claims_plans_from_before_accounts(app_store: InMemoryStore) -> None:
    plan = TradePlan.start(
        stock_id=1,
        category=HoldingCategory.D50,
        start_date=date(2026, 10, 1),
        planned_end_date=date(2026, 11, 20),
        entry_price=Decimal(100),
        target_pct=Decimal(10),
    )
    plan.id = 99
    app_store.plans[99] = plan  # no owner: started before user accounts existed

    with new_client(app_store) as admin:
        sign_in(admin)
        assert [p["id"] for p in admin.get("/api/trade-plans").json()] == [99]


def test_disabled_users_are_signed_out_and_refused(
    app_store: InMemoryStore, admin: TestClient
) -> None:
    code = invite(admin)
    with new_client(app_store) as user:
        sign_in(user, "u@x.io", code)
        user_id = user.get("/api/auth/me").json()["id"]
        me_admin = admin.get("/api/auth/me").json()["id"]
        assert (
            admin.put(
                f"/api/admin/users/{me_admin}/disabled", json={"is_disabled": True}
            ).status_code
            == 403
        )
        assert (
            admin.put(
                f"/api/admin/users/{user_id}/disabled", json={"is_disabled": True}
            ).status_code
            == 200
        )
        assert user.get("/api/auth/me").status_code == 401
        again = user.post("/api/auth/dev-login", json={"email": "u@x.io"})
        assert "disabled" in again.json()["detail"]
    actions = [e["action"] for e in admin.get("/api/admin/audit").json()]
    assert {"sign_up", "sign_in", "invite_created", "user_disabled"} <= set(actions)


def test_delete_account_removes_everything(app_store: InMemoryStore, admin: TestClient) -> None:
    code = invite(admin)
    with new_client(app_store) as user:
        sign_in(user, "gone@x.io", code)
        user.post("/api/trade-plans", json=PLAN)
        user.put("/api/watchlist/INFY")
        user_id = user.get("/api/auth/me").json()["id"]

        assert user.delete("/api/auth/me").status_code == 204
        assert user.get("/api/auth/me").status_code == 401
    assert all(str(u) != user_id for u in app_store.users)
    assert all(str(p.owner_id) != user_id for p in app_store.plans.values())
    assert not [s for s in app_store.sessions.values() if str(s.user_id) == user_id]
    deleted = next(e for e in app_store.audit if e.action == "account_deleted")
    assert deleted.user_id is None and deleted.details == {}  # no personal data kept


def test_watchlist(admin: TestClient) -> None:
    assert admin.put("/api/watchlist/INFY").status_code == 204
    assert admin.put("/api/watchlist/TCS").status_code == 204
    assert admin.put("/api/watchlist/INFY").status_code == 204  # no duplicate
    assert [s["symbol"] for s in admin.get("/api/watchlist").json()] == ["INFY", "TCS"]
    assert admin.delete("/api/watchlist/INFY").status_code == 204
    assert [s["symbol"] for s in admin.get("/api/watchlist").json()] == ["TCS"]
    assert admin.put("/api/watchlist/NOPE").status_code == 404
