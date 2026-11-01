from fastapi.testclient import TestClient

from tests.eodhd_fixtures import VALID_TOKEN


def providers(client: TestClient) -> dict[str, dict[str, object]]:
    return {p["plugin_name"]: p for p in client.get("/api/admin/providers").json()}


def test_mock_and_eodhd_are_listed_mock_is_primary(client: TestClient) -> None:
    listed = providers(client)

    assert set(listed) == {"mock", "eodhd"}
    assert listed["mock"]["is_primary"] is True
    assert listed["eodhd"]["credential_fields"] == ["api_token"]
    assert listed["eodhd"]["has_credentials"] is False
    assert client.post("/api/admin/providers/mock/test").json()["is_ok"] is True


def test_credentials_are_write_only(client: TestClient) -> None:
    saved = client.put(
        "/api/admin/providers/eodhd/credentials", json={"values": {"api_token": VALID_TOKEN}}
    )

    assert saved.status_code == 204
    body = client.get("/api/admin/providers").text
    assert VALID_TOKEN not in body
    assert providers(client)["eodhd"]["credential_hints"] == {"api_token": "1a2b"}
    test = client.post("/api/admin/providers/eodhd/test").json()
    assert test["is_ok"] is True and "API calls used today" in test["message"]


def test_credential_validation(client: TestClient) -> None:
    short = {"values": {"api_token": "abc"}}
    unknown = {"values": {"password": "long-enough-value"}}

    assert client.put("/api/admin/providers/eodhd/credentials", json=short).status_code == 503
    assert client.put("/api/admin/providers/eodhd/credentials", json=unknown).status_code == 503
    assert client.put("/api/admin/providers/nope/credentials", json=short).status_code == 404


def test_primary_needs_credentials_and_blocks_removal(client: TestClient) -> None:
    assert client.put("/api/admin/providers/eodhd/primary").status_code == 503
    untested = client.post("/api/admin/providers/eodhd/test").json()
    assert untested["is_ok"] is False and "add the api_token" in untested["message"]

    client.put(
        "/api/admin/providers/eodhd/credentials", json={"values": {"api_token": VALID_TOKEN}}
    )
    assert client.put("/api/admin/providers/eodhd/primary").status_code == 204
    assert providers(client)["eodhd"]["is_primary"] is True
    assert client.delete("/api/admin/providers/eodhd/credentials").status_code == 503

    assert client.put("/api/admin/providers/mock/primary").status_code == 204
    assert client.delete("/api/admin/providers/eodhd/credentials").status_code == 204
    assert providers(client)["eodhd"]["has_credentials"] is False


def test_unknown_provider_returns_404(client: TestClient) -> None:
    assert client.post("/api/admin/providers/nope/test").status_code == 404
