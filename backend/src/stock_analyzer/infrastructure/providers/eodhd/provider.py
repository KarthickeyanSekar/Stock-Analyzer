"""EODHD plugin: NSE daily prices and quarterly fundamentals (https://eodhd.com/financial-apis).

Endpoints: ``/api/eod/{SYMBOL}.NSE`` (``date, open, high, low, close, adjusted_close, volume``),
``/api/v1.1/fundamentals/{SYMBOL}.NSE`` with ``filter`` (10 API calls per request) and
``/api/user`` (quota). The API token travels as a query parameter, so it never appears in our
logs or error messages (httpx request logging is silenced in ``configure_logging``).
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

logger = logging.getLogger(__name__)

PLUGIN_NAME = "eodhd"
BASE_URL = "https://eodhd.com"
EXCHANGE_SUFFIX = "NSE"
CRORE = Decimal(10_000_000)
CENTS = Decimal("0.01")
REPORT_LAG = timedelta(days=45)  # SEBI allows 45 days for quarterly results
QUARTERS_PER_YEAR = 4
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
AUTH_STATUSES = frozenset({401, 403})
FUNDAMENTAL_FILTERS = (
    "Financials::Income_Statement::quarterly",
    "Financials::Balance_Sheet::quarterly",
    "Earnings::History",
)


def _decimal(value: Any) -> Decimal | None:  # noqa: ANN401 - raw JSON value
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _section(data: Mapping[str, Any], path: str) -> dict[str, Any]:
    """A filtered section: EODHD may return it nested or keyed by the filter path."""
    if path in data and isinstance(data[path], dict):
        return dict(data[path])
    node: Any = data
    for part in path.split("::"):
        if not isinstance(node, dict) or part not in node:
            return {}
        node = node[part]
    return dict(node) if isinstance(node, dict) else {}


class EodhdProvider:
    """Implements ``MarketDataProvider`` and ``FundamentalsProvider`` for NSE stocks."""

    def __init__(
        self,
        api_token: str,
        client: httpx.Client | None = None,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Use ``api_token``; ``client`` and ``sleep`` are injectable for tests."""
        if not api_token:
            raise ProviderError("EODHD needs an API token: add it in Admin > Providers")
        self._token = api_token
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=30.0)
        self._max_retries = max_retries
        self._sleep = sleep

    @property
    def name(self) -> str:
        """Plugin name stored as ``source_provider``."""
        return PLUGIN_NAME

    def _get(self, path: str, params: Mapping[str, str] | None = None) -> Any:  # noqa: ANN401
        query = {"api_token": self._token, "fmt": "json", **(params or {})}
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.get(path, params=query)
            except httpx.HTTPError as error:
                if attempt == self._max_retries:
                    raise ProviderError(f"EODHD unreachable ({type(error).__name__})") from None
                self._sleep(2**attempt)
                continue
            if response.status_code in AUTH_STATUSES:
                raise ProviderError(
                    f"EODHD rejected the API key or plan (HTTP {response.status_code}): "
                    "check it in Admin > Providers"
                )
            if response.status_code in RETRY_STATUSES and attempt < self._max_retries:
                self._sleep(2**attempt)
                continue
            if response.status_code == httpx.codes.NOT_FOUND:
                return None
            if response.status_code != httpx.codes.OK:
                raise ProviderError(f"EODHD request failed (HTTP {response.status_code})")
            return response.json()
        raise ProviderError("EODHD request failed after retries")  # pragma: no cover

    def list_instruments(self) -> Sequence[Stock]:
        """The NIFTY 50 universe (same symbols and sectors as the POC), labelled ``eodhd``."""
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
        """Daily candles with EODHD's split/dividend ``adjusted_close``."""
        rows = self._get(
            f"/api/eod/{symbol}.{EXCHANGE_SUFFIX}",
            {"from": start.isoformat(), "to": end.isoformat(), "period": "d"},
        )
        candles, skipped = [], 0
        for row in rows or []:
            values = [_decimal(row.get(k)) for k in ("open", "high", "low", "close")]
            adjusted = _decimal(row.get("adjusted_close")) or values[3]
            if any(v is None for v in values) or adjusted is None:
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
                        adj_close=adjusted,
                        volume=int(float(row.get("volume") or 0)),
                    )
                )
            except (ValueError, KeyError):
                skipped += 1  # inconsistent OHLC or bad date: never stored
        if skipped:
            logger.warning("%s: skipped %d invalid EODHD rows", symbol, skipped)
        return candles

    def quarterly_fundamentals(
        self, symbol: str, start: date, end: date
    ) -> Sequence[QuarterlyFundamentals]:
        """Quarters ending ``start``..``end`` and announced by ``end`` (point-in-time)."""
        data = self._get(
            f"/api/v1.1/fundamentals/{symbol}.{EXCHANGE_SUFFIX}",
            {"filter": ",".join(FUNDAMENTAL_FILTERS)},
        )
        if not isinstance(data, dict):
            return []
        income = _section(data, FUNDAMENTAL_FILTERS[0])
        balance = _section(data, FUNDAMENTAL_FILTERS[1])
        earnings = _section(data, FUNDAMENTAL_FILTERS[2])
        quarters = []
        for key in sorted(income):
            quarter = self._quarter(key, income[key], balance.get(key), earnings.get(key))
            if quarter and start <= quarter.period_end <= end and quarter.is_known_on(end):
                quarters.append(quarter)
        return quarters

    @staticmethod
    def _quarter(
        key: str,
        income: Mapping[str, Any],
        balance: Mapping[str, Any] | None,
        earnings: Mapping[str, Any] | None,
    ) -> QuarterlyFundamentals | None:
        """Map one EODHD quarter; ``None`` when a required figure is missing."""
        if not balance:
            return None
        try:
            period_end = date.fromisoformat(key)
        except ValueError:
            return None
        revenue = _decimal(income.get("totalRevenue"))
        profit = _decimal(income.get("netIncome"))
        equity = _decimal(balance.get("totalStockholderEquity"))
        shares = _decimal(balance.get("commonStockSharesOutstanding"))
        debt = _decimal(balance.get("shortLongTermDebtTotal"))
        if debt is None:
            debt = (_decimal(balance.get("shortTermDebt")) or Decimal(0)) + (
                _decimal(balance.get("longTermDebt")) or Decimal(0)
            )
        if None in (revenue, profit, equity, shares) or not equity or not shares:
            return None
        assert revenue is not None and profit is not None  # noqa: S101 - narrowed above
        if equity <= 0 or shares <= 0 or revenue < 0:
            return None
        eps = _decimal((earnings or {}).get("epsActual")) or profit / shares
        reported = (earnings or {}).get("reportDate")
        announced = period_end + REPORT_LAG
        if isinstance(reported, str):
            with contextlib.suppress(ValueError):
                announced = max(date.fromisoformat(reported), period_end + timedelta(days=1))
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
        """Call ``/api/user`` and report the daily quota."""
        try:
            user = self._get("/api/user")
        except ProviderError as error:
            return ConnectionCheck(is_ok=False, message=str(error))
        if not isinstance(user, dict):
            return ConnectionCheck(is_ok=False, message="EODHD returned no account details")
        used, limit = user.get("apiRequests"), user.get("dailyRateLimit")
        plan = user.get("subscriptionType") or "plan"
        return ConnectionCheck(
            is_ok=True, message=f"Connected ({plan}): {used} of {limit} API calls used today"
        )
