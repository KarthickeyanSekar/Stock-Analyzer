from fastapi.testclient import TestClient


def test_every_endpoint_has_a_summary_and_every_response_an_example(client: TestClient) -> None:
    spec = client.get("/api/openapi.json").json()

    operations = [op for path in spec["paths"].values() for op in path.values()]
    assert all(op.get("summary") for op in operations)
    responses = {
        name: schema
        for name, schema in spec["components"]["schemas"].items()
        if name.endswith("Response")
    }
    assert responses
    assert [name for name, schema in responses.items() if not schema.get("examples")] == []
