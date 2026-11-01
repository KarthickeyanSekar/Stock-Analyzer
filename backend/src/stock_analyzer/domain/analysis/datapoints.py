"""Data point calculators from docs/21-stock-analysis-datapoints.md (pure Python, no I/O).

Statistical inputs are floats (Q64); every function returns ``None`` when there is not enough
history, so missing values stay missing instead of becoming misleading zeros. Callers pass only
data known on the analysis date (point-in-time); these functions never look anything up.
"""

import math
from collections.abc import Sequence
from itertools import pairwise

TRADING_DAYS_PER_YEAR = 252
MONTH = 21


def sma(values: Sequence[float], window: int) -> float | None:
    """Simple moving average of the last ``window`` values."""
    if window <= 0 or len(values) < window:
        return None
    return sum(values[-window:]) / window


def price_vs_ma(closes: Sequence[float], window: int) -> float | None:
    """Close ÷ moving average - 1 (e.g., 0.05 = 5% above the 50-DMA)."""
    average = sma(closes, window)
    return closes[-1] / average - 1 if average else None


def golden_cross(closes: Sequence[float]) -> float | None:
    """1.0 when the 50-DMA is above the 200-DMA (golden cross), else 0.0."""
    fast, slow = sma(closes, 50), sma(closes, 200)
    if fast is None or slow is None:
        return None
    return 1.0 if fast > slow else 0.0


def distance_from_high(
    closes: Sequence[float], window: int = TRADING_DAYS_PER_YEAR
) -> float | None:
    """Close ÷ highest close of the window - 1 (0 at a new high, negative below it)."""
    if len(closes) < window:
        return None
    return closes[-1] / max(closes[-window:]) - 1


def distance_from_low(closes: Sequence[float], window: int = TRADING_DAYS_PER_YEAR) -> float | None:
    """Close ÷ lowest close of the window - 1 (0 at a new low, positive above it)."""
    if len(closes) < window:
        return None
    return closes[-1] / min(closes[-window:]) - 1


def momentum(closes: Sequence[float], lookback: int, skip: int = 0) -> float | None:
    """Return over ``lookback`` days, ignoring the most recent ``skip`` days (12-1M momentum)."""
    if len(closes) <= lookback:
        return None
    end = closes[-1 - skip]
    start = closes[-1 - lookback]
    return end / start - 1


def daily_returns(closes: Sequence[float]) -> list[float]:
    """Simple daily returns."""
    return [b / a - 1 for a, b in pairwise(closes)]


def volatility(closes: Sequence[float], window: int = TRADING_DAYS_PER_YEAR) -> float | None:
    """Annualised standard deviation of daily returns over ``window`` days."""
    if len(closes) <= window:
        return None
    returns = daily_returns(closes[-window - 1 :])
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(TRADING_DAYS_PER_YEAR)


def atr_pct(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], window: int = 14
) -> float | None:
    """Average true range over ``window`` days ÷ the last close."""
    if len(closes) <= window:
        return None
    true_ranges = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(len(closes) - window, len(closes))
    ]
    return sum(true_ranges) / window / closes[-1]


def max_drawdown(closes: Sequence[float], window: int = TRADING_DAYS_PER_YEAR) -> float | None:
    """Largest peak-to-trough fall within the window (e.g., -0.25 = -25%)."""
    if len(closes) < window:
        return None
    peak, worst = closes[-window], 0.0
    for price in closes[-window:]:
        peak = max(peak, price)
        worst = min(worst, price / peak - 1)
    return worst


def beta(
    stock_returns: Sequence[float],
    market_returns: Sequence[float],
    window: int = TRADING_DAYS_PER_YEAR,
) -> float | None:
    """Covariance with the market ÷ market variance over the last ``window`` returns."""
    if len(stock_returns) < window or len(market_returns) < window:
        return None
    s, m = stock_returns[-window:], market_returns[-window:]
    mean_s, mean_m = sum(s) / window, sum(m) / window
    covariance = sum((a - mean_s) * (b - mean_m) for a, b in zip(s, m, strict=True))
    variance = sum((b - mean_m) ** 2 for b in m)
    return covariance / variance if variance else None


def volume_trend(volumes: Sequence[float]) -> float | None:
    """20-day average volume ÷ 100-day average volume."""
    recent, longer = sma(volumes, 20), sma(volumes, 100)
    return recent / longer if recent is not None and longer else None


def pe_ratio(price: float, eps_ttm: float | None) -> float | None:
    """Price ÷ trailing-twelve-month EPS (``None`` for losses: P/E is not meaningful)."""
    if eps_ttm is None or eps_ttm <= 0:
        return None
    return price / eps_ttm


def pb_ratio(price: float, book_value_per_share: float | None) -> float | None:
    """Price ÷ book value per share."""
    if not book_value_per_share or book_value_per_share <= 0:
        return None
    return price / book_value_per_share


def earnings_yield(price: float, eps_ttm: float | None) -> float | None:
    """TTM EPS ÷ price (the inverse of P/E, defined for losses too)."""
    if eps_ttm is None or price <= 0:
        return None
    return eps_ttm / price


def growth(current: float | None, previous: float | None) -> float | None:
    """Current ÷ previous - 1 (e.g., quarterly year-on-year growth)."""
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def cagr(end: float | None, start: float | None, years: float) -> float | None:
    """Compound annual growth rate: (end ÷ start)^(1/years) - 1."""
    if end is None or start is None or start <= 0 or end <= 0 or years <= 0:
        return None
    result: float = (end / start) ** (1 / years) - 1
    return result


def peg_ratio(pe: float | None, eps_growth: float | None) -> float | None:
    """P/E ÷ EPS growth in percent (only for positive growth)."""
    if pe is None or eps_growth is None or eps_growth <= 0:
        return None
    return pe / (eps_growth * 100)


def graham_number(eps_ttm: float | None, book_value_per_share: float | None) -> float | None:
    """√(22.5 x EPS x BVPS): Graham's upper bound for a defensive buy price."""
    if not eps_ttm or not book_value_per_share or eps_ttm <= 0 or book_value_per_share <= 0:
        return None
    return math.sqrt(22.5 * eps_ttm * book_value_per_share)


def percentile_ranks(values: dict[int, float | None]) -> dict[int, float | None]:
    """Cross-sectional percentile (0-1) of each value within one date; ties share the average."""
    present = sorted((v, k) for k, v in values.items() if v is not None)
    ranks: dict[int, float | None] = dict.fromkeys(values)
    if len(present) == 1:
        ranks[present[0][1]] = 0.5
        return ranks
    i = 0
    while i < len(present):
        j = i
        while j + 1 < len(present) and present[j + 1][0] == present[i][0]:
            j += 1
        average = (i + j) / 2 / (len(present) - 1)
        for _, key in present[i : j + 1]:
            ranks[key] = average
        i = j + 1
    return ranks


# --- Short-term technicals (docs/02-short-term-analyzer.md; Phase 7) ---------------------


def ema(values: Sequence[float], span: int) -> list[float]:
    """Exponential moving average series (seeded with the first value)."""
    if not values:
        return []
    alpha = 2 / (span + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return result


def rsi(closes: Sequence[float], window: int = 14) -> float | None:
    """Relative strength index (0-100) with Wilder's smoothing."""
    if len(closes) <= window:
        return None
    changes = daily_changes(closes)
    gains = [max(c, 0.0) for c in changes]
    losses = [max(-c, 0.0) for c in changes]
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    for gain, loss in zip(gains[window:], losses[window:], strict=True):
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def daily_changes(closes: Sequence[float]) -> list[float]:
    """Price differences between consecutive closes."""
    return [b - a for a, b in pairwise(closes)]


def macd_histogram_pct(closes: Sequence[float]) -> float | None:
    """MACD(12, 26) minus its 9-day signal line, as a share of the price."""
    if len(closes) < 35:  # noqa: PLR2004 - 26 + 9 sessions for a settled signal line
        return None
    macd = [fast - slow for fast, slow in zip(ema(closes, 12), ema(closes, 26), strict=True)]
    return (macd[-1] - ema(macd, 9)[-1]) / closes[-1]


def ema_gap(closes: Sequence[float], fast: int = 9, slow: int = 21) -> float | None:
    """EMA(fast) ÷ EMA(slow) - 1: positive in a short-term up-trend."""
    if len(closes) < slow:
        return None
    return ema(closes, fast)[-1] / ema(closes, slow)[-1] - 1


def bollinger_pct_b(closes: Sequence[float], window: int = 20, width: float = 2.0) -> float | None:
    """Where the close sits in the Bollinger band: 0 = lower band, 1 = upper band."""
    if len(closes) < window:
        return None
    recent = closes[-window:]
    mean = sum(recent) / window
    std = math.sqrt(sum((c - mean) ** 2 for c in recent) / window)
    if std == 0:
        return 0.5
    return (closes[-1] - (mean - width * std)) / (2 * width * std)


def obv_trend(closes: Sequence[float], volumes: Sequence[float], window: int = 20) -> float | None:
    """On-balance volume change over the window ÷ volume traded in it (-1 … 1)."""
    if len(closes) <= window or len(volumes) < len(closes):
        return None
    flow = 0.0
    for i in range(len(closes) - window, len(closes)):
        direction = (closes[i] > closes[i - 1]) - (closes[i] < closes[i - 1])
        flow += direction * volumes[i]
    traded = sum(volumes[len(closes) - window : len(closes)])
    return flow / traded if traded else None


def volume_spike(volumes: Sequence[float], window: int = 20) -> float | None:
    """Last session's volume ÷ the average of the previous ``window`` sessions."""
    if len(volumes) <= window:
        return None
    average = sum(volumes[-window - 1 : -1]) / window
    return volumes[-1] / average if average else None
