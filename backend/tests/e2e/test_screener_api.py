import asyncio
import copy
from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from stock_analyzer.application.use_cases.ml.build_features import BuildFeaturesAndLabels
from stock_analyzer.main import create_app
from tests.conftest import make_container, sign_in
from tests.fakes import FakeUnitOfWork, InMemoryStore


@pytest.fixture(scope="module")
def featured_store(seeded_store: InMemoryStore) -> InMemoryStore:
    store = copy.deepcopy(seeded_store)
    asyncio.run(BuildFeaturesAndLabels(lambda: FakeUnitOfWork(store)).execute())
    return store


@pytest.fixture
def api(featured_store: InMemoryStore) -> Iterator[TestClient]:
    with TestClient(create_app(make_container(featured_store))) as client:
        sign_in(client)
        yield client


def screen(api: TestClient, **params: object) -> list[dict[str, object]]:
    response = api.get("/api/screener", params={"category": "1Y", "target_pct": 10} | params)
    assert response.status_code == 200, response.text
    rows: list[dict[str, object]] = response.json()
    return rows


def test_results_are_ranked_by_the_target_probability(api: TestClient) -> None:
    rows = screen(api)

    assert len(rows) == 50
    probabilities = [r["probability"] for r in rows]
    assert probabilities == sorted(probabilities, reverse=True)  # type: ignore[type-var]
    assert all(r["prediction"]["category"] == "1Y" for r in rows)  # type: ignore[index]
    assert all(isinstance(r["quality"], int) for r in rows)


def test_each_filter_narrows_the_result(api: TestClient) -> None:
    everything = screen(api)
    likely = screen(api, min_probability=0.5)
    safe = screen(api, min_worst_pct=-10)
    quality = screen(api, min_quality=6)
    sector = screen(api, sector="Information Technology")

    assert all(r["probability"] >= 0.5 for r in likely)  # type: ignore[operator]
    assert all(r["prediction"]["p10_pct"] >= -10 for r in safe)  # type: ignore[index]
    assert all(r["quality"] >= 6 for r in quality)  # type: ignore[operator]
    assert {r["stock"]["sector"] for r in sector} == {"Information Technology"}  # type: ignore[index]
    for subset in (likely, safe, quality, sector):
        assert 0 < len(subset) < len(everything)


def test_target_range_reports_both_ends(api: TestClient) -> None:
    rows = screen(api, target_pct=10, target_max_pct=20)

    assert all(r["probability_max"] <= r["probability"] for r in rows)  # type: ignore[operator]
    assert api.get("/api/screener", params={"category": "1Y", "target_pct": 0}).status_code == 422
    assert screen(api, target_pct=50, min_probability=1) == []


def test_predictions_mark_the_best_risk_adjusted_period(api: TestClient) -> None:
    body = api.get("/api/stocks/INFY/predictions").json()
    scored = {
        p["category"]: p["p50_pct"] / (p["p50_pct"] - p["p10_pct"])
        for p in body["predictions"]
        if p["p50_pct"] > 0 and p["p50_pct"] > p["p10_pct"]
    }

    if scored:
        assert body["best_category"] == max(scored, key=lambda c: scored[c])
    else:
        assert body["best_category"] is None


def test_analogs_only_use_finished_setups(api: TestClient) -> None:
    body = api.get("/api/stocks/INFY/analogs", params={"category": "50D", "limit": 15}).json()

    assert len(body["cases"]) == 15
    latest = date.fromisoformat(body["as_of"])
    assert all(date.fromisoformat(c["as_of"]) < latest - timedelta(days=50) for c in body["cases"])
    similarities = [c["similarity"] for c in body["cases"]]
    assert similarities == sorted(similarities, reverse=True)
    assert body["median_return_pct"] is not None
    assert set(body["hit_rates"]) == {"5", "10", "15", "20", "25", "30", "40", "50"}
    assert api.get("/api/stocks/NOPE/analogs").status_code == 404
