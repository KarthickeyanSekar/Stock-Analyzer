from fastapi.testclient import TestClient


def test_search_finds_stocks_by_symbol_or_name(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/stocks", params={"query": "bank", "limit": 50})

    assert response.status_code == 200
    symbols = {s["symbol"] for s in response.json()}
    assert {"HDFCBANK", "ICICIBANK", "AXISBANK"} <= symbols
    assert all(s["is_synthetic"] for s in response.json())


def test_prices_are_filtered_by_date(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/api/stocks/INFY/prices", params={"from": "2026-10-01", "to": "2026-10-31"}
    )

    assert response.status_code == 200
    days = [c["date"] for c in response.json()]
    assert days and all("2026-10-01" <= d <= "2026-10-31" for d in days)


def test_predictions_cover_every_category_with_ordered_ranges(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/stocks/RELIANCE/predictions")

    assert response.status_code == 200
    body = response.json()
    categories = [p["category"] for p in body["predictions"]]
    assert set(categories) >= {"50D", "100D", "200D", "300D", "1Y"}  # 2Y/3Y need more history
    for p in body["predictions"]:
        assert p["p10_pct"] <= p["p50_pct"] <= p["p90_pct"]
        assert (p["cagr_p50_pct"] is not None) == (p["category"] in {"1Y", "2Y", "3Y"})
    assert body["last_close"]["date"] == "2026-10-30"


def test_unknown_stock_returns_404(seeded_client: TestClient) -> None:
    assert seeded_client.get("/api/stocks/NOPE").status_code == 404


def test_overview_lists_every_stock_with_moves_and_1y_prediction(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/stocks/overview")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 50
    reliance = next(r for r in rows if r["stock"]["symbol"] == "RELIANCE")
    assert reliance["last_date"] == "2026-10-30"
    assert reliance["day_change_pct"] is not None
    assert reliance["return_1y_pct"] is not None
    assert reliance["median_1y_pct"] is not None
    assert 0 <= reliance["prob_up_1y"] <= 1
