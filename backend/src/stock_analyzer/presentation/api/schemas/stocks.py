"""Stock, price and prediction response models.

Numbers are sent as JSON numbers for charts and display; all calculations happen
server-side with ``Decimal``. Percentages are percent points (``9.5`` = +9.5%).
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from stock_analyzer.application.use_cases.stocks.queries import StockOverview
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import Prediction
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock

SYNTHETIC_PROVIDERS = frozenset({"mock"})


class StockResponse(BaseModel):
    """A stock and whether its data is synthetic (shown with a SYNTHETIC badge)."""

    symbol: str
    name: str
    exchange: str
    market: str
    sector: str | None
    currency: str
    is_synthetic: bool

    @classmethod
    def from_domain(cls, stock: Stock) -> "StockResponse":
        """Map a domain stock."""
        return cls(
            symbol=stock.symbol,
            name=stock.name,
            exchange=stock.exchange,
            market=stock.market_code,
            sector=stock.sector,
            currency=stock.currency,
            is_synthetic=stock.source_provider in SYNTHETIC_PROVIDERS,
        )


class CandleResponse(BaseModel):
    """One daily candle."""

    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int

    @classmethod
    def from_domain(cls, candle: Candle) -> "CandleResponse":
        """Map a domain candle."""
        return cls(
            date=candle.trade_date,
            open=float(candle.open),
            high=float(candle.high),
            low=float(candle.low),
            close=float(candle.close),
            adj_close=float(candle.adj_close),
            volume=candle.volume,
        )


def _cagr_pct(total_pct: Decimal, calendar_days: int) -> float:
    """Annualise a total return: (1 + r) ** (365 / days) - 1."""
    growth: float = (1 + float(total_pct) / 100) ** (365 / calendar_days)
    return round((growth - 1) * 100, 2)


class PredictionResponse(BaseModel):
    """Prediction for one holding category (headline = median % with range + target odds)."""

    category: HoldingCategory
    calendar_days: int
    as_of: date
    p10_pct: float
    p50_pct: float
    p90_pct: float
    prob_up: float = Field(description="Share of past windows that ended higher (0-1)")
    prob_hit: dict[str, float] = Field(description="Target % → probability before the stop")
    cagr_p50_pct: float | None = Field(description="Median per year; only for 1Y and longer")
    model_version: str

    @classmethod
    def from_domain(cls, prediction: Prediction) -> "PredictionResponse":
        """Map a domain prediction."""
        category = prediction.category
        return cls(
            category=category,
            calendar_days=category.calendar_days,
            as_of=prediction.as_of,
            p10_pct=float(prediction.range.p10_pct),
            p50_pct=float(prediction.range.p50_pct),
            p90_pct=float(prediction.range.p90_pct),
            prob_up=float(prediction.prob_up),
            prob_hit={str(t): float(p) for t, p in sorted(prediction.prob_hit.items())},
            cagr_p50_pct=(
                _cagr_pct(prediction.range.p50_pct, category.calendar_days)
                if category.shows_cagr
                else None
            ),
            model_version=prediction.model_version,
        )


class StockPredictionsResponse(BaseModel):
    """A stock, its last close and the latest prediction per holding category."""

    stock: StockResponse
    last_close: CandleResponse | None
    predictions: list[PredictionResponse]


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


class StockOverviewResponse(BaseModel):
    """One row of the Stocks table."""

    stock: StockResponse
    last_close: float | None
    last_date: date | None
    day_change_pct: float | None
    return_1y_pct: float | None
    median_1y_pct: float | None
    prob_up_1y: float | None

    @classmethod
    def from_domain(cls, row: StockOverview) -> "StockOverviewResponse":
        """Map a stock overview row."""
        return cls(
            stock=StockResponse.from_domain(row.stock),
            last_close=float(row.last_close.close) if row.last_close else None,
            last_date=row.last_close.trade_date if row.last_close else None,
            day_change_pct=_num(row.day_change_pct),
            return_1y_pct=_num(row.return_1y_pct),
            median_1y_pct=_num(row.median_1y_pct),
            prob_up_1y=_num(row.prob_up_1y),
        )
