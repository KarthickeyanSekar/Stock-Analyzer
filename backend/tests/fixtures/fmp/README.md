# FMP fixtures

Hand-made responses in the shape of the FMP stable API (`/stable/...`), replayed by
`tests/fmp_fixtures.py` through `httpx.MockTransport`. No real data, no API key.
The 2026-10-29 candle is deliberately inconsistent (open above high) and must be skipped;
the 2025-12-31 quarter has no net income and must be skipped.
