"""Replay FMP-shaped responses through httpx.MockTransport (no network)."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx

FIXTURES = Path(__file__).parent / "fixtures" / "fmp"
VALID_KEY = "fmp-test-key-3c4d"  # gitleaks:allow (fake key, fake transport only)
ROUTES = {
    "/stable/historical-price-eod/full": "eod_full",
    "/stable/historical-price-eod/dividend-adjusted": "eod_adjusted",
    "/stable/income-statement": "income",
    "/stable/balance-sheet-statement": "balance",
    "/stable/quote": "quote",
}


def handler(
    responses: dict[str, list[int]] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """Route by path and ``symbol``; ``responses`` queues status codes per path first."""
    queued = {k: list(v) for k, v in (responses or {}).items()}

    def route(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("apikey") != VALID_KEY:
            return httpx.Response(401, json={"Error Message": "Invalid API KEY."})
        path = request.url.path
        if queued.get(path):
            return httpx.Response(queued[path].pop(0))
        if path not in ROUTES:
            return httpx.Response(404)
        file = FIXTURES / f"{ROUTES[path]}_{request.url.params.get('symbol')}.json"
        # FMP answers an unknown symbol with an empty list.
        return httpx.Response(200, json=json.loads(file.read_text()) if file.exists() else [])

    return route


def client(responses: dict[str, list[int]] | None = None) -> httpx.Client:
    """An httpx client that serves the fixtures."""
    return httpx.Client(
        base_url="https://financialmodelingprep.com",
        transport=httpx.MockTransport(handler(responses)),
    )
