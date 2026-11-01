"""Holding-period screener and similar past setups (docs/16-holding-period-screener.md)."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.analysis.features import FEATURE_SET_VERSION, embedding
from stock_analyzer.domain.analysis.quality import quality_score
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.baseline import _quantile
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS, Prediction
from stock_analyzer.domain.prediction.screening import (
    Candidate,
    ScreenCriteria,
    probability_of,
    screen,
)
from stock_analyzer.domain.stock.stock import Stock

MAX_STOCKS = 10_000
DEFAULT_ANALOGS = 20


@dataclass(frozen=True, slots=True)
class ScreenRow:
    """One screener result."""

    stock: Stock
    prediction: Prediction
    probability: Decimal | None  # of the requested target
    probability_max: Decimal | None  # of the upper end of a target range
    quality: int | None


@dataclass(frozen=True, slots=True)
class AnalogCase:
    """A similar past setup of any stock, with its outcome."""

    symbol: str
    as_of: date
    similarity: float  # 1 - cosine distance
    return_pct: float
    is_stopped: bool


@dataclass(frozen=True, slots=True)
class AnalogSummary:
    """What happened after the setups most similar to a stock's latest one."""

    symbol: str
    category: HoldingCategory
    as_of: date | None
    cases: list[AnalogCase]
    median_return_pct: float | None
    share_up: float | None
    hit_rates: dict[int, float]


class ScreenerQueries:
    """Read-only screener queries."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work per query."""
        self._uow_factory = uow_factory

    async def screen(self, criteria: ScreenCriteria) -> list[ScreenRow]:
        """Stocks whose latest prediction meets the criteria, best first."""
        async with self._uow_factory() as uow:
            stocks = {s.id: s for s in await uow.stocks.search(None, MAX_STOCKS)}
            predictions = await uow.predictions.latest_for_category(criteria.category)
            latest = await uow.features.latest_features(FEATURE_SET_VERSION)
        candidates = [
            Candidate(
                symbol=stocks[p.stock_id].symbol,
                sector=stocks[p.stock_id].sector,
                prediction=p,
                quality=quality_score(latest[p.stock_id][1]) if p.stock_id in latest else None,
            )
            for p in predictions
            if p.stock_id in stocks
        ]
        by_symbol = {s.symbol: s for s in stocks.values()}
        return [
            ScreenRow(
                stock=by_symbol[c.symbol],
                prediction=c.prediction,
                probability=probability_of(c.prediction, criteria.target_pct),
                probability_max=(
                    probability_of(c.prediction, criteria.target_max_pct)
                    if criteria.target_max_pct
                    else None
                ),
                quality=c.quality,
            )
            for c in screen(candidates, criteria)
        ]

    async def analogs(
        self, symbol: str, category: HoldingCategory, limit: int = DEFAULT_ANALOGS
    ) -> AnalogSummary:
        """The ``limit`` most similar past setups whose holding period had ended by today."""
        async with self._uow_factory() as uow:
            stock = await uow.stocks.get_by_symbol(symbol)
            if stock is None or stock.id is None:
                raise NotFoundError(f"stock {symbol} not found")
            latest = (await uow.features.latest_features(FEATURE_SET_VERSION)).get(stock.id)
            if latest is None:
                return AnalogSummary(symbol, category, None, [], None, None, {})
            as_of, features = latest
            # Only setups whose whole holding period lies before today: no peeking ahead.
            before = as_of - timedelta(days=category.calendar_days)
            found = await uow.features.nearest(
                FEATURE_SET_VERSION, embedding(features), category, before, limit
            )
            symbols = {s.id: s.symbol for s in await uow.stocks.search(None, MAX_STOCKS)}
        cases = [
            AnalogCase(
                symbol=symbols.get(a.stock_id, "?"),
                as_of=a.as_of,
                similarity=round(1 - a.distance, 4),
                return_pct=round(a.label.forward_return_pct, 2),
                is_stopped=a.label.is_stopped,
            )
            for a in found
        ]
        returns = sorted(a.label.forward_return_pct for a in found)
        n = len(found)
        return AnalogSummary(
            symbol=symbol,
            category=category,
            as_of=as_of,
            cases=cases,
            median_return_pct=round(_quantile(returns, 0.5), 2) if n else None,
            share_up=round(sum(r > 0 for r in returns) / n, 4) if n else None,
            hit_rates={t: round(sum(a.label.hits[t] for a in found) / n, 4) for t in TARGET_PCTS}
            if n
            else {},
        )
