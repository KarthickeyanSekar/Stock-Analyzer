"""Financial Modeling Prep plugin: NSE daily prices and quarterly fundamentals.

Stable API (https://site.financialmodelingprep.com/developer/docs), NSE tickers use ``.NS``:
``/stable/historical-price-eod/full`` (OHLCV), ``/stable/historical-price-eod/dividend-adjusted``
(``adjClose``), ``/stable/income-statement`` and ``/stable/balance-sheet-statement`` with
``period=quarter``, and ``/stable/quote`` for the connection test. Indian stocks usually need a
paid FMP plan (HTTP 402 otherwise). The key travels as the ``apikey`` query parameter, so it
never appears in our logs or error messages (httpx request logging is silenced).
"""

import contextlib
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from stock_analyzer.application.errors import ProviderError
from stock_analyzer.application.ports.market_data import ConnectionCheck
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock
from stock_analyzer.infrastructure.providers.mock.universe import NIFTY50
from stock_analyzer.infrastructure.providers.raw_archive import RawResponseArchive

logger = logging.getLogger(__name__)

PLUGIN_NAME = "fmp"
BASE_URL = "https://financialmodelingprep.com"
EXCHANGE_SUFFIX = "NS"
CRORE = Decimal(10_000_000)
CENTS = Decimal("0.01")
REPORT_LAG = timedelta(days=45)  # SEBI allows 45 days for quarterly results
QUARTERS_PER_YEAR = 4
QUARTERS_LIMIT = "60"  # 15 years of quarters in one request
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
AUTH_STATUSES = frozenset({401, 403})
PAYMENT_REQUIRED = 402
TEST_SYMBOL = "RELIANCE"


def _decimal(value: Any) -> Decimal | None:  # noqa: ANN401 - raw JSON value
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _ticker(symbol: str) -> str:
    return f"{symbol}.{EXCHANGE_SUFFIX}"


class FmpProvider:
    """Implements ``MarketDataProvider`` and ``FundamentalsProvider`` for NSE stocks."""

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        archive: RawResponseArchive | None = None,
    ) -> None:
        """Use ``api_key``; ``client`` and ``sleep`` are injectable for tests."""
        if not api_key:
            raise ProviderError("FMP needs an API key: add it in Admin > Providers")
        self._key = api_key
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=30.0)
        self._max_retries = max_retries
        self._sleep = sleep
        self._archive = archive

    @property
    def name(self) -> str:
        """Plugin name stored as ``source_provider``."""
        return PLUGIN_NAME

    def _get(self, path: str, params: Mapping[str, str]) -> Any:  # noqa: ANN401
        query = {**params, "apikey": self._key}
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.get(path, params=query)
            except httpx.HTTPError as error:
                if attempt == self._max_retries:
                    raise ProviderError(f"FMP unreachable ({type(error).__name__})") from None
                self._sleep(2**attempt)
                continue
            if response.status_code in AUTH_STATUSES:
                raise ProviderError(
                    f"FMP rejected the API key (HTTP {response.status_code}): "
                    "check it in Admin > Providers"
                )
            if response.status_code == PAYMENT_REQUIRED:
                raise ProviderError(
                    "FMP plan does not include this data (HTTP 402): NSE stocks need a paid plan"
                )
            if response.status_code in RETRY_STATUSES and attempt < self._max_retries:
                self._sleep(2**attempt)
                continue
            if response.status_code == httpx.codes.NOT_FOUND:
                return None
            if response.status_code != httpx.codes.OK:
                raise ProviderError(f"FMP request failed (HTTP {response.status_code})")
            data = response.json()
            if self._archive is not None:
                self._archive.save(self.name, path, params, data)
            # FMP reports some errors as HTTP 200 with {"Error Message": "..."}.
            if isinstance(data, dict) and "Error Message" in data:
                raise ProviderError("FMP refused the request: check the key and plan")
            return data
        raise ProviderError("FMP request failed after retries")  # pragma: no cover

    def list_instruments(self) -> Sequence[Stock]:
        """The NIFTY 50 universe (same symbols and sectors as the POC), labelled ``fmp``."""
        return [
            Stock(
                market_code="IN",
                exchange="NSE",
                symbol=symbol,
                name=name,
                sector=sector,
                currency="INR",
                timezone="Asia/Kolkata",
                source_provider=PLUGIN_NAME,
            )
            for symbol, name, sector in NIFTY50
        ]

    def daily_candles(self, symbol: str, start: date, end: date) -> Sequence[Candle]:
        """Daily OHLCV joined with FMP's dividend-adjusted close (falls back to close)."""
        params = {"symbol": _ticker(symbol), "from": start.isoformat(), "to": end.isoformat()}
        rows = self._get("/stable/historical-price-eod/full", params)
        if not rows:
            return []
        adjusted_rows = self._get("/stable/historical-price-eod/dividend-adjusted", params) or []
        adjusted = {r.get("date"): _decimal(r.get("adjClose")) for r in adjusted_rows}
        candles, skipped = [], 0
        for row in sorted(rows, key=lambda r: str(r.get("date"))):
            values = [_decimal(row.get(k)) for k in ("open", "high", "low", "close")]
            if any(v is None for v in values):
                skipped += 1
                continue
            o, h, low, c = (v for v in values if v is not None)
            try:
                candles.append(
                    Candle(
                        trade_date=date.fromisoformat(row["date"]),
                        open=o,
                        high=h,
                        low=low,
                        close=c,
                        adj_close=adjusted.get(row["date"]) or c,
                        volume=int(float(row.get("volume") or 0)),
                    )
                )
            except (ValueError, KeyError):
                skipped += 1  # inconsistent OHLC or bad date: never stored
        if skipped:
            logger.warning("%s: skipped %d invalid FMP rows", symbol, skipped)
        return candles

    def quarterly_fundamentals(
        self, symbol: str, start: date, end: date
    ) -> Sequence[QuarterlyFundamentals]:
        """Quarters ending ``start``..``end`` and announced by ``end`` (point-in-time)."""
        params = {"symbol": _ticker(symbol), "period": "quarter", "limit": QUARTERS_LIMIT}
        income = self._get("/stable/income-statement", params)
        if not isinstance(income, list) or not income:
            return []
        balance_rows = self._get("/stable/balance-sheet-statement", params) or []
        balance = {r.get("date"): r for r in balance_rows if isinstance(r, dict)}
        quarters = []
        for row in sorted(income, key=lambda r: str(r.get("date"))):
            quarter = self._quarter(row, balance.get(row.get("date")))
            if quarter and start <= quarter.period_end <= end and quarter.is_known_on(end):
                quarters.append(quarter)
        return quarters

    @staticmethod
    def _quarter(
        income: Mapping[str, Any], balance: Mapping[str, Any] | None
    ) -> QuarterlyFundamentals | None:
        """Map one FMP quarter; ``None`` when a required figure is missing."""
        if not balance:
            return None
        try:
            period_end = date.fromisoformat(str(income.get("date")))
        except ValueError:
            return None
        revenue = _decimal(income.get("revenue"))
        profit = _decimal(income.get("netIncome"))
        shares = _decimal(income.get("weightedAverageShsOut"))
        equity = _decimal(balance.get("totalStockholdersEquity"))
        debt = _decimal(balance.get("totalDebt")) or Decimal(0)
        if revenue is None or profit is None or not equity or not shares:
            return None
        if equity <= 0 or shares <= 0 or revenue < 0:
            return None
        eps = _decimal(income.get("eps")) or profit / shares
        announced = period_end + REPORT_LAG
        filed = income.get("filingDate")
        if isinstance(filed, str):
            with contextlib.suppress(ValueError):
                announced = max(date.fromisoformat(filed[:10]), period_end + timedelta(days=1))
        return QuarterlyFundamentals(
            period_end=period_end,
            announced_date=announced,
            revenue_cr=(revenue / CRORE).quantize(CENTS),
            net_profit_cr=(profit / CRORE).quantize(CENTS),
            eps=eps.quantize(CENTS),
            book_value_per_share=(equity / shares).quantize(CENTS),
            roe_pct=(profit * QUARTERS_PER_YEAR / equity * 100).quantize(CENTS),
            debt_to_equity=(debt / equity).quantize(CENTS),
        )

    def test_connection(self) -> ConnectionCheck:
        """Fetch one NSE quote: proves the key works and the plan covers India."""
        try:
            quote = self._get("/stable/quote", {"symbol": _ticker(TEST_SYMBOL)})
        except ProviderError as error:
            return ConnectionCheck(is_ok=False, message=str(error))
        if not isinstance(quote, list) or not quote:
            return ConnectionCheck(
                is_ok=False, message="FMP returned no NSE quote: the plan may not cover India"
            )
        price = quote[0].get("price")
        return ConnectionCheck(
            is_ok=True, message=f"Connected: NSE data available ({TEST_SYMBOL} {price})"
        )
