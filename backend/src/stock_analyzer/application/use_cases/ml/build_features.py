"""Build point-in-time features and training labels for every stock (``make features``)."""

from dataclasses import dataclass
from datetime import date

from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.analysis.features import (
    FEATURE_SET_VERSION,
    AdjustedSeries,
    Features,
    add_ranks,
    build_features,
    equal_weight_returns,
)
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.labels import Label, make_label

MAX_STOCKS = 10_000
SAMPLE_STEP = 5  # one sample per week: less overlap between neighbouring labels, far less work
WARMUP_DAYS = 200  # trend features need ~200 sessions of history


@dataclass(frozen=True, slots=True)
class BuildResult:
    """How much was written."""

    dates: int
    features: int
    labels: int


def sample_dates(days: list[date], step: int = SAMPLE_STEP) -> list[date]:
    """Every ``step``-th trading day after the warm-up, always including the last day."""
    picked = days[WARMUP_DAYS::step]
    if days and (not picked or picked[-1] != days[-1]):
        picked.append(days[-1])
    return picked


class BuildFeaturesAndLabels:
    """Idempotent: re-running replaces rows of the same feature-set version."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Read prices and fundamentals, write features and labels, with fresh units of work."""
        self._uow_factory = uow_factory

    async def execute(self) -> BuildResult:
        """Build features for every sample date and labels for every holding category."""
        series: dict[int, AdjustedSeries] = {}
        quarters: dict[int, list[QuarterlyFundamentals]] = {}
        async with self._uow_factory() as uow:
            for stock in await uow.stocks.search(None, MAX_STOCKS):
                if stock.id is None:  # pragma: no cover
                    continue
                candles = await uow.prices.get_candles(stock.id)
                if candles:
                    series[stock.id] = AdjustedSeries.from_candles(candles)
                    quarters[stock.id] = await uow.fundamentals.list_quarters(stock.id)
        if not series:
            return BuildResult(0, 0, 0)
        market = equal_weight_returns(series)
        dates = sample_dates(sorted(market))

        feature_rows: list[tuple[int, date, Features]] = []
        for as_of in dates:
            by_stock: dict[int, Features] = {}
            for stock_id, s in series.items():
                end = _index_on_or_before(s.days, as_of)
                if end is None:
                    continue
                known = [q for q in quarters[stock_id] if q.is_known_on(as_of)]
                by_stock[stock_id] = build_features(as_of, _slice(s, end + 1), market, known)
            feature_rows.extend((k, as_of, f) for k, f in add_ranks(by_stock).items())

        label_rows: dict[HoldingCategory, list[tuple[int, date, Label]]] = {}
        for category in HoldingCategory:
            rows = label_rows.setdefault(category, [])
            for stock_id, s in series.items():
                positions = {day: i for i, day in enumerate(s.days)}
                for as_of in dates:
                    i = positions.get(as_of)
                    if i is None:
                        continue
                    label = make_label(s.closes[i + 1 :], s.closes[i], category.approx_trading_days)
                    if label is not None:
                        rows.append((stock_id, as_of, label))

        async with self._uow_factory() as uow:
            written = await uow.features.upsert_features(FEATURE_SET_VERSION, feature_rows)
            labels = sum(
                [await uow.features.upsert_labels(c, rows) for c, rows in label_rows.items()]
            )
            await uow.commit()
        return BuildResult(dates=len(dates), features=written, labels=labels)


def _index_on_or_before(days: list[date], as_of: date) -> int | None:
    """Index of the last day ≤ ``as_of`` (binary search), or ``None``."""
    lo, hi = 0, len(days)
    while lo < hi:
        mid = (lo + hi) // 2
        if days[mid] <= as_of:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1 if lo else None


def _slice(s: AdjustedSeries, end: int) -> AdjustedSeries:
    """The series up to (excluding) ``end``: only data known on that day."""
    return AdjustedSeries(
        days=s.days[:end],
        closes=s.closes[:end],
        highs=s.highs[:end],
        lows=s.lows[:end],
        volumes=s.volumes[:end],
        last_raw_close=s.raw_closes[end - 1],
        raw_closes=s.raw_closes[:end],
    )
