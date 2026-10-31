from fastapi.testclient import TestClient


def test_mock_provider_is_listed_and_testable(seeded_client: TestClient) -> None:
    providers = seeded_client.get("/api/admin/providers").json()

    assert [p["plugin_name"] for p in providers] == ["mock"]
    assert seeded_client.post("/api/admin/providers/mock/test").json()["is_ok"] is True


def test_unknown_provider_returns_404(seeded_client: TestClient) -> None:
    assert seeded_client.post("/api/admin/providers/nope/test").status_code == 404
