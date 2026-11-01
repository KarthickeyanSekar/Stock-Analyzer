"""Replay recorded-shape EODHD responses through httpx.MockTransport (no network)."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx

FIXTURES = Path(__file__).parent / "fixtures" / "eodhd"
VALID_TOKEN = "test-token-1a2b"  # noqa: S105 - fake key, only matches this fake transport


def handler(
    responses: dict[str, list[int]] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """Route by path; ``responses`` queues status codes per path before the fixture is served."""
    queued = {k: list(v) for k, v in (responses or {}).items()}

    def route(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("api_token") != VALID_TOKEN:
            return httpx.Response(401, json={"error": "Unauthenticated"})
        path = request.url.path
        if queued.get(path):
            return httpx.Response(queued[path].pop(0))
        if path == "/api/user":
            name = "user.json"
        elif path.startswith("/api/eod/"):
            name = f"eod_{path.rsplit('/', 1)[1]}.json"
        elif path.startswith("/api/v1.1/fundamentals/"):
            name = f"fundamentals_{path.rsplit('/', 1)[1]}.json"
        else:
            return httpx.Response(404)
        file = FIXTURES / name
        if not file.exists():
            return httpx.Response(404, json={"error": "Ticker not found"})
        return httpx.Response(200, json=json.loads(file.read_text()))

    return route


def client(responses: dict[str, list[int]] | None = None) -> httpx.Client:
    """An httpx client that serves the fixtures."""
    return httpx.Client(
        base_url="https://eodhd.com", transport=httpx.MockTransport(handler(responses))
    )
