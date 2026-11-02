import copy

from fastapi.testclient import TestClient

from stock_analyzer.main import create_app
from tests.conftest import make_container, sign_in
from tests.fakes import InMemoryStore


def test_lists_sources_and_limits_picks_to_five(seeded_store: InMemoryStore) -> None:
    with TestClient(create_app(make_container(copy.deepcopy(seeded_store)))) as client:
        sign_in(client)
        check(client)


def check(client: TestClient) -> None:
    body = client.get("/api/admin/data-sources").json()

    assert body["max_real_sync"] == 5
    stocks = body["stocks"]
    assert stocks and all(s["is_real"] is False and s["latest_source"] == "mock" for s in stocks)
    for stock in stocks[:5]:
        picked = client.put(
            f"/api/admin/data-sources/{stock['symbol']}/real-sync", json={"is_enabled": True}
        )
        assert picked.status_code == 204
    sixth = client.put(
        f"/api/admin/data-sources/{stocks[5]['symbol']}/real-sync", json={"is_enabled": True}
    )
    assert sixth.status_code == 422 and "at most 5" in sixth.json()["detail"]
    after = client.get("/api/admin/data-sources").json()["stocks"]
    assert sum(s["is_real_sync_enabled"] for s in after) == 5
    assert '"real_sync_enabled"' in client.get("/api/admin/audit").text
