from fastapi.testclient import TestClient


def start_plan(client: TestClient, **body: object) -> dict[str, object]:
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


def test_close_calculates_success_partial_and_failure(seeded_client: TestClient) -> None:
    cases = {"1104": "SUCCESS", "1150": "PARTIAL", "1090": "FAILURE"}  # target +10% on 1000
    for exit_price, expected in cases.items():
        plan = start_plan(seeded_client, entry_price=1000, target_pct=10)
        response = seeded_client.post(
            f"/api/trade-plans/{plan['id']}/close",
            json={"exit_date": "2026-12-21", "exit_price": exit_price},
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == expected


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
