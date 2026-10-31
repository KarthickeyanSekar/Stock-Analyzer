from fastapi.testclient import TestClient

from tests.conftest import FIXED_NOW


def test_health_reports_ok_with_env_and_time(client: TestClient) -> None:
    # Act
    response = client.get("/api/health")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["env"] == "test"
    assert body["server_time"] == FIXED_NOW.isoformat().replace("+00:00", "Z")
