from typing import Any

from fastapi.testclient import TestClient


def start_plan(client: TestClient, **body: object) -> dict[str, Any]:
    payload = {"symbol": "INFY", "category": "50D", "start_date": "2026-10-30"} | body
    response = client.post("/api/trade-plans", json=payload)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def stocks_by_1y_median(client: TestClient) -> tuple[str, str]:
    """Return (a symbol with a positive 1Y median, a symbol with a negative one)."""
    medians = {}
    for stock in client.get("/api/stocks", params={"limit": 100}).json():
        body = client.get(f"/api/stocks/{stock['symbol']}/predictions").json()
        one_year = next(p for p in body["predictions"] if p["category"] == "1Y")
        medians[stock["symbol"]] = one_year["p50_pct"]
    positive = next(symbol for symbol, median in medians.items() if median > 0)
    negative = next(symbol for symbol, median in medians.items() if median <= 0)
    return positive, negative


def test_start_plan_uses_close_and_locks_the_prediction(seeded_client: TestClient) -> None:
    symbol, _ = stocks_by_1y_median(seeded_client)
    predictions = seeded_client.get(f"/api/stocks/{symbol}/predictions").json()
    one_year = next(p for p in predictions["predictions"] if p["category"] == "1Y")

    plan = start_plan(seeded_client, symbol=symbol, category="1Y")

    assert plan["status"] == "ACTIVE"
    assert plan["entry_price"] == predictions["last_close"]["close"]
    assert plan["target_pct"] == one_year["p50_pct"]  # default target = predicted median
    assert plan["prediction_id"] is not None
    assert plan["planned_end_date"] == "2027-11-01"  # +365 days is a Saturday → Monday
    assert plan["success_tolerance_pp"] == 0.5


def test_no_default_target_when_the_prediction_is_not_positive(seeded_client: TestClient) -> None:
    _, symbol = stocks_by_1y_median(seeded_client)
    body = {"symbol": symbol, "category": "1Y", "start_date": "2026-10-30"}

    response = seeded_client.post("/api/trade-plans", json=body)

    assert response.status_code == 422
    assert "enter a target" in response.json()["detail"]
    assert start_plan(seeded_client, symbol=symbol, category="1Y", target_pct=8)["target_pct"] == 8


def test_close_judges_against_the_locked_prediction(seeded_client: TestClient) -> None:
    # Q31: the outcome compares the actual return with the prediction, not the own target.
    cases = {0: "SUCCESS", 5: "PARTIAL", -5: "FAILURE"}  # pp away from the prediction
    for offset_pp, expected in cases.items():
        plan = start_plan(seeded_client, entry_price=1000, target_pct=10)
        assert plan["benchmark_pct"] == plan["predicted_pct"]
        exit_price = round(1000 * (1 + (plan["predicted_pct"] + offset_pp) / 100), 2)
        response = seeded_client.post(
            f"/api/trade-plans/{plan['id']}/close",
            json={"exit_date": "2026-12-21", "exit_price": exit_price},
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == expected


def test_own_target_is_kept_apart_from_the_prediction(seeded_client: TestClient) -> None:
    symbol, _ = stocks_by_1y_median(seeded_client)
    plan = start_plan(seeded_client, symbol=symbol, category="1Y", target_pct=30)
    assert plan["target_pct"] == 30
    assert plan["predicted_pct"] is not None and plan["predicted_pct"] != 30
    exit_price = round(plan["entry_price"] * (1 + plan["predicted_pct"] / 100), 2)

    closed = seeded_client.post(
        f"/api/trade-plans/{plan['id']}/close",
        json={"exit_date": "2027-11-01", "exit_price": exit_price},
    ).json()

    assert closed["outcome"] == "SUCCESS"  # the model was right …
    assert closed["is_own_target_met"] is False  # … but your own +30% wasn't reached
    assert closed["own_target_gap_pp"] < 0


def test_entry_price_is_the_close_unless_typed(seeded_client: TestClient) -> None:
    by_close = start_plan(seeded_client)
    typed = start_plan(seeded_client, entry_price=1234.5)

    assert by_close["entry_source"] == "CLOSE"
    assert by_close["entry_price"] == by_close["reference_close"]
    assert typed["entry_source"] == "MANUAL"
    assert typed["entry_price"] == 1234.5
    assert typed["reference_close"] == by_close["reference_close"]  # Q29: both kept


def test_active_plans_carry_their_progress(seeded_client: TestClient) -> None:
    running = start_plan(seeded_client, start_date="2026-09-15")  # 50D: ends in November
    ended = start_plan(seeded_client, start_date="2026-06-01")  # 50D: ended in July

    progress = seeded_client.get(f"/api/trade-plans/{running['id']}").json()["progress"]
    finished = seeded_client.get(f"/api/trade-plans/{ended['id']}").json()["progress"]

    assert progress["as_of"] == "2026-10-30"  # the last synthetic close
    assert 0 < progress["day_number"] < progress["total_days"]
    assert 0 <= progress["progress_pct"] <= 100
    assert not progress["is_end_date_reached"]
    assert finished["as_of"] == ended["planned_end_date"]  # progress stops at the end date
    assert finished["day_number"] == finished["total_days"]
    assert finished["is_end_date_reached"]


def test_preview_sizes_the_position_from_settings(seeded_client: TestClient) -> None:
    payload = {"symbol": "INFY", "category": "50D", "start_date": "2026-10-30", "stop_pct": -5}
    plans_before = len(seeded_client.get("/api/trade-plans").json())

    preview = seeded_client.post("/api/trade-plans/preview", json=payload).json()

    # 1% of 10,00,000 at a 5% stop = 2,00,000 budget, whole shares only
    assert preview["risk_amount"] == 10000
    assert preview["suggested_quantity"] == int(200000 // preview["entry_price"])
    assert preview["suggested_amount"] <= 200000
    assert len(seeded_client.get("/api/trade-plans").json()) == plans_before  # nothing saved


def test_settings_are_defaults_for_new_plans_only(seeded_client: TestClient) -> None:
    before = start_plan(seeded_client)
    settings: dict[str, float] = {
        "paper_capital": 500000,
        "risk_pct": 2,
        "success_tolerance_pp": 1,
        "default_stop_pct": -10,
    }
    assert seeded_client.put("/api/settings/journal", json=settings).status_code == 200

    after = start_plan(seeded_client)
    unchanged = seeded_client.get(f"/api/trade-plans/{before['id']}").json()

    assert seeded_client.get("/api/settings/journal").json() == settings
    assert (after["stop_pct"], after["success_tolerance_pp"]) == (-10, 1)
    assert (unchanged["stop_pct"], unchanged["success_tolerance_pp"]) == (-7, 0.5)
    bad = settings | {"risk_pct": 50}
    assert seeded_client.put("/api/settings/journal", json=bad).status_code == 422
    defaults = {**settings, "paper_capital": 1000000, "risk_pct": 1}
    defaults |= {"success_tolerance_pp": 0.5, "default_stop_pct": -7}
    seeded_client.put("/api/settings/journal", json=defaults)  # the store is shared


def test_closing_twice_returns_409(seeded_client: TestClient) -> None:
    plan = start_plan(seeded_client, entry_price=1000, target_pct=10)
    close = {"exit_date": "2026-12-21", "exit_price": 1100}

    assert seeded_client.post(f"/api/trade-plans/{plan['id']}/close", json=close).status_code == 200
    assert seeded_client.post(f"/api/trade-plans/{plan['id']}/close", json=close).status_code == 409


def test_invalid_input_is_rejected(seeded_client: TestClient) -> None:
    bad_target = {"symbol": "INFY", "category": "50D", "start_date": "2026-10-30", "target_pct": -5}
    unknown = {"symbol": "NOPE", "category": "50D", "start_date": "2026-10-30"}

    assert seeded_client.post("/api/trade-plans", json=bad_target).status_code == 422
    assert seeded_client.post("/api/trade-plans", json=unknown).status_code == 404
    assert seeded_client.get("/api/trade-plans/99999").status_code == 404


def test_list_returns_plans_newest_first(seeded_client: TestClient) -> None:
    first = start_plan(seeded_client, entry_price=1000, target_pct=5)
    second = start_plan(seeded_client, entry_price=1000, target_pct=6)

    ids = [p["id"] for p in seeded_client.get("/api/trade-plans").json()]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_summary_counts_outcomes_and_model_bias(client: TestClient) -> None:
    # An empty journal first
    empty = client.get("/api/trade-plans/summary").json()
    assert empty["active"] == 0 and empty["closed"] == 0 and empty["success_rate"] is None


def test_summary_reflects_closed_plans(seeded_client: TestClient) -> None:
    before = seeded_client.get("/api/trade-plans/summary").json()
    plan = start_plan(seeded_client, entry_price=1000, target_pct=10)
    seeded_client.post(
        f"/api/trade-plans/{plan['id']}/close",
        json={"exit_date": "2026-12-21", "exit_price": 1150},  # +15% vs +10% → PARTIAL, bias +5
    )

    after = seeded_client.get("/api/trade-plans/summary").json()

    assert after["closed"] == before["closed"] + 1
    assert after["outcomes"]["PARTIAL"] == before["outcomes"]["PARTIAL"] + 1
    assert set(after["outcomes"]) == {"SUCCESS", "PARTIAL", "FAILURE", "EXITED_EARLY"}
    fifty = next(r for r in after["by_category"] if r["category"] == "50D")
    assert fifty["closed"] >= 1
