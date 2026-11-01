"""Point-in-time feature vectors for the ML engine (docs/26-ml-pipeline.md §2).

``build_features`` sees only what is passed in, and callers pass only data known on ``as_of``:
candles up to that day and fundamentals announced by then. Changing the feature list or a
formula requires a new ``FEATURE_SET_VERSION`` (never a silent change).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from stock_analyzer.domain.analysis import datapoints as dp
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.pricing.candle import Candle

FEATURE_SET_VERSION = "fs-v1"
QUARTERS_PER_YEAR = 4

FEATURE_NAMES: tuple[str, ...] = (
    # Price & trend
    "price_vs_50dma",
    "price_vs_200dma",
    "golden_cross",
    "dist_52w_high",
    "dist_52w_low",
    "mom_3m",
    "mom_6m",
    "mom_12_1m",
    "rel_strength_6m",
    "volatility_1y",
    "atr_pct",
    "max_drawdown_1y",
    "beta_1y",
    "volume_trend",
    # Valuation
    "pe",
    "pb",
    "earnings_yield",
    "peg",
    "price_to_graham",
    # Profitability, growth, health
    "roe",
    "net_margin",
    "revenue_yoy",
    "eps_ttm_yoy",
    "revenue_cagr_3y",
    "debt_to_equity",
)
# Ranked within the universe on each date (cross-sectional normalisation).
RANKED_FEATURES: tuple[str, ...] = (
    "mom_6m",
    "mom_12_1m",
    "rel_strength_6m",
    "volatility_1y",
    "earnings_yield",
    "pb",
    "roe",
    "revenue_yoy",
)
ALL_FEATURES: tuple[str, ...] = FEATURE_NAMES + tuple(f"{name}_rank" for name in RANKED_FEATURES)

Features = dict[str, float | None]


@dataclass(frozen=True, slots=True)
class AdjustedSeries:
    """Split-adjusted daily series (high/low scaled by each day's adjustment factor)."""

    days: list[date]
    closes: list[float]
    highs: list[float]
    lows: list[float]
    volumes: list[float]
    last_raw_close: float
    raw_closes: list[float]

    @classmethod
    def from_candles(cls, candles: Sequence[Candle]) -> "AdjustedSeries":
        """Build the series from candles in date order."""
        factors = [float(c.adj_close / c.close) for c in candles]
        return cls(
            days=[c.trade_date for c in candles],
            closes=[float(c.adj_close) for c in candles],
            highs=[float(c.high) * f for c, f in zip(candles, factors, strict=True)],
            lows=[float(c.low) * f for c, f in zip(candles, factors, strict=True)],
            volumes=[float(c.volume) for c in candles],
            last_raw_close=float(candles[-1].close),
            raw_closes=[float(c.close) for c in candles],
        )


def equal_weight_returns(series: Mapping[int, AdjustedSeries]) -> dict[date, float]:
    """Daily return of an equal-weight index of every stock (the market context)."""
    by_day: dict[date, list[float]] = {}
    for s in series.values():
        for day, ret in zip(s.days[1:], dp.daily_returns(s.closes), strict=True):
            by_day.setdefault(day, []).append(ret)
    return {day: sum(values) / len(values) for day, values in sorted(by_day.items())}


def _ttm(quarters: Sequence[QuarterlyFundamentals], field: str, offset: int = 0) -> float | None:
    """Sum of ``field`` over 4 quarters ending ``offset`` quarters before the latest."""
    end = len(quarters) - offset
    if end < QUARTERS_PER_YEAR:
        return None
    return sum(float(getattr(q, field)) for q in quarters[end - QUARTERS_PER_YEAR : end])


def _fundamental_features(price: float, quarters: Sequence[QuarterlyFundamentals]) -> Features:
    if not quarters:
        return dict.fromkeys(FEATURE_NAMES[14:])
    latest = quarters[-1]
    eps_ttm = _ttm(quarters, "eps")
    bvps = float(latest.book_value_per_share)
    revenue_ttm = _ttm(quarters, "revenue_cr")
    profit_ttm = _ttm(quarters, "net_profit_cr")
    pe = dp.pe_ratio(price, eps_ttm)
    eps_growth = dp.growth(eps_ttm, _ttm(quarters, "eps", offset=QUARTERS_PER_YEAR))
    graham = dp.graham_number(eps_ttm, bvps)
    year_ago = quarters[-1 - QUARTERS_PER_YEAR] if len(quarters) > QUARTERS_PER_YEAR else None
    return {
        "pe": pe,
        "pb": dp.pb_ratio(price, bvps),
        "earnings_yield": dp.earnings_yield(price, eps_ttm),
        "peg": dp.peg_ratio(pe, eps_growth),
        "price_to_graham": price / graham if graham else None,
        "roe": float(latest.roe_pct) / 100,
        "net_margin": profit_ttm / revenue_ttm if profit_ttm and revenue_ttm else None,
        "revenue_yoy": dp.growth(
            float(latest.revenue_cr), float(year_ago.revenue_cr) if year_ago else None
        ),
        "eps_ttm_yoy": eps_growth,
        "revenue_cagr_3y": dp.cagr(
            revenue_ttm, _ttm(quarters, "revenue_cr", offset=3 * QUARTERS_PER_YEAR), 3
        ),
        "debt_to_equity": float(latest.debt_to_equity),
    }


def build_features(
    as_of: date,
    series: AdjustedSeries,
    market: Mapping[date, float],
    quarters: Sequence[QuarterlyFundamentals],
) -> Features:
    """Return the feature vector on ``as_of`` (``None`` = not enough history).

    Raises ``ValueError`` if any input is dated after ``as_of`` (look-ahead guard).
    """
    if series.days and series.days[-1] > as_of:
        raise ValueError("candles after as_of were passed to build_features")
    if any(not q.is_known_on(as_of) for q in quarters):
        raise ValueError("fundamentals announced after as_of were passed to build_features")
    closes = series.closes
    stock_returns = dp.daily_returns(closes)
    market_returns = [market.get(day, 0.0) for day in series.days[1:]]
    market_6m = None
    if len(market_returns) >= 6 * dp.MONTH:
        growth_6m = 1.0
        for ret in market_returns[-6 * dp.MONTH :]:
            growth_6m *= 1 + ret
        market_6m = growth_6m - 1
    mom_6m = dp.momentum(closes, 6 * dp.MONTH)
    features: Features = {
        "price_vs_50dma": dp.price_vs_ma(closes, 50),
        "price_vs_200dma": dp.price_vs_ma(closes, 200),
        "golden_cross": dp.golden_cross(closes),
        "dist_52w_high": dp.distance_from_high(closes),
        "dist_52w_low": dp.distance_from_low(closes),
        "mom_3m": dp.momentum(closes, 3 * dp.MONTH),
        "mom_6m": mom_6m,
        "mom_12_1m": dp.momentum(closes, 12 * dp.MONTH, skip=dp.MONTH),
        "rel_strength_6m": mom_6m - market_6m
        if mom_6m is not None and market_6m is not None
        else None,
        "volatility_1y": dp.volatility(closes),
        "atr_pct": dp.atr_pct(series.highs, series.lows, closes),
        "max_drawdown_1y": dp.max_drawdown(closes),
        "beta_1y": dp.beta(stock_returns, market_returns),
        "volume_trend": dp.volume_trend(series.volumes),
    }
    features.update(_fundamental_features(series.last_raw_close, quarters))
    return features


def add_ranks(by_stock: Mapping[int, Features]) -> dict[int, Features]:
    """Add ``<feature>_rank`` (0-1 within the universe on one date) for ``RANKED_FEATURES``."""
    result = {stock_id: dict(features) for stock_id, features in by_stock.items()}
    for name in RANKED_FEATURES:
        ranks = dp.percentile_ranks({k: f.get(name) for k, f in by_stock.items()})
        for stock_id, rank in ranks.items():
            result[stock_id][f"{name}_rank"] = rank
    return result
