"""Phase 5 validation: point-in-time backtest, calibration review, journal review, verdict.

The live predictor (empirical baseline; docs/26 §4) is recomputed on each rebalance date from
prices up to that date only, so every simulated plan is out-of-sample. The benchmark is the
equal-weight universe (synthetic data) until a NIFTY 50 index series is available.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.analysis.features import AdjustedSeries, equal_weight_returns
from stock_analyzer.domain.journal.trade_plan import PlanOutcome, PlanStatus, TradePlan
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction import evaluation as ev
from stock_analyzer.domain.prediction.baseline import empirical_prediction
from stock_analyzer.domain.prediction.labels import DEFAULT_STOP_PCT, make_label
from stock_analyzer.domain.validation.backtest import (
    CostModel,
    Trade,
    TradeSummary,
    simulate,
    summarise,
)
from stock_analyzer.domain.validation.reliability import ReliabilityRow, reliability

MAX_STOCKS = 10_000
WARMUP_DAYS = 252  # the baseline needs about a year of history
REBALANCE_EVERY = 40  # trading days between plan starts
TOP_N = 5
BASELINE_STEP = 10
MIN_JOURNAL_PLANS = 30
# The return each holding period aims for in the backtest strategy.
STRATEGY_TARGETS: dict[HoldingCategory, int] = {
    HoldingCategory.D50: 5,
    HoldingCategory.D100: 10,
    HoldingCategory.D200: 10,
    HoldingCategory.D300: 15,
    HoldingCategory.Y1: 20,
}


@dataclass(slots=True)
class CategoryValidation:
    """Everything the report says about one holding period."""

    category: HoldingCategory
    target_pct: int
    summary: TradeSummary | None = None
    trades: list[Trade] = field(default_factory=list)
    reliability: list[ReliabilityRow] = field(default_factory=list)
    ece_pp: float | None = None
    coverage: float | None = None
    journal_closed: int = 0
    journal_outcomes: dict[str, int] = field(default_factory=dict)
    verdict: str = "not decidable"
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationReport:
    """The whole validation run."""

    is_synthetic: bool
    benchmark: str
    data_start: date | None
    data_end: date | None
    categories: list[CategoryValidation]


def verdict(v: CategoryValidation, is_synthetic: bool) -> tuple[str, list[str]]:
    """Q70: go only if every criterion holds; synthetic data is never evidence."""
    reasons = []
    if is_synthetic:
        reasons.append("synthetic data")
    if v.summary is None or not v.summary.beats_benchmark:
        reasons.append("net expectancy does not beat the benchmark")
    if v.ece_pp is None or v.ece_pp > ev.MAX_ECE_PP:
        reasons.append("calibration error above 5 pp")
    if v.coverage is None or not ev.COVERAGE_MIN <= v.coverage <= ev.COVERAGE_MAX:
        reasons.append("80% range coverage outside 75-85%")
    if v.journal_closed < MIN_JOURNAL_PLANS:
        reasons.append(f"fewer than {MIN_JOURNAL_PLANS} closed journal plans")
    else:
        good = v.journal_outcomes.get("SUCCESS", 0) + v.journal_outcomes.get("PARTIAL", 0)
        if good < v.journal_outcomes.get("FAILURE", 0):
            reasons.append("journal failures outnumber successes")
    if is_synthetic:
        return "not decidable", reasons
    return ("go" if not reasons else "no-go"), reasons


class RunValidation:
    """``make validate``."""

    def __init__(self, uow_factory: UnitOfWorkFactory, costs: CostModel | None = None) -> None:
        """Validate with ``costs`` (defaults: Q69)."""
        self._uow_factory = uow_factory
        self._costs = costs or CostModel()

    async def execute(self) -> ValidationReport:
        """Run the backtest, calibration and journal review."""
        async with self._uow_factory() as uow:
            stocks = await uow.stocks.search(None, MAX_STOCKS)
            series = {}
            exact: dict[str, list[tuple[date, Decimal]]] = {}  # the baseline wants Decimals
            for stock in stocks:
                if stock.id is not None and (candles := await uow.prices.get_candles(stock.id)):
                    series[stock.id] = (stock.symbol, AdjustedSeries.from_candles(candles))
                    exact[stock.symbol] = [(c.trade_date, c.adj_close) for c in candles]
            plans = await uow.trade_plans.list_all()
        is_synthetic = any(s.source_provider == "mock" for s in stocks)
        market = equal_weight_returns({k: s for k, (_, s) in series.items()})
        days = sorted(market)
        index = [1.0]
        for day in days:
            index.append(index[-1] * (1 + market[day]))
        index_by_day = dict(zip(days, index[1:], strict=True))
        rebalance = days[WARMUP_DAYS::REBALANCE_EVERY]

        results = [
            self._category(
                category=category,
                target=target,
                series=series,
                exact=exact,
                index_by_day=index_by_day,
                rebalance=rebalance,
                plans=plans,
            )
            for category, target in STRATEGY_TARGETS.items()
        ]
        for v in results:
            v.verdict, v.reasons = verdict(v, is_synthetic)
        return ValidationReport(
            is_synthetic=is_synthetic,
            benchmark="equal-weight universe" if is_synthetic else "equal-weight NIFTY 50",
            data_start=days[0] if days else None,
            data_end=days[-1] if days else None,
            categories=results,
        )

    def _category(  # noqa: PLR0913 - the shared inputs of one holding period's validation
        self,
        *,
        category: HoldingCategory,
        target: int,
        series: dict[int, tuple[str, AdjustedSeries]],
        exact: dict[str, list[tuple[date, Decimal]]],
        index_by_day: dict[date, float],
        rebalance: list[date],
        plans: list[TradePlan],
    ) -> CategoryValidation:
        """Backtest, calibrate and review the journal for one holding period."""
        v = CategoryValidation(category, target)
        horizon = category.approx_trading_days
        trades: list[Trade] = []
        outcomes: list[bool] = []
        probs: list[float] = []
        actual: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for as_of in rebalance:
            scored = []
            for symbol, s in series.values():
                if as_of not in s.days:
                    continue
                i = s.days.index(as_of)
                prediction = empirical_prediction(
                    stock_id=0,
                    as_of=as_of,
                    category=category,
                    closes=exact[symbol][: i + 1],
                    step=BASELINE_STEP,
                )
                label = make_label(s.closes[i + 1 :], s.closes[i], horizon)
                if prediction is None or label is None:
                    continue
                prob = float(prediction.prob_hit[target])
                outcomes.append(label.hits[target])
                probs.append(prob)
                actual.append(label.forward_return_pct)
                lows.append(float(prediction.range.p10_pct))
                highs.append(float(prediction.range.p90_pct))
                scored.append((prob, symbol, s, i))
            for prob, symbol, s, i in sorted(scored, key=lambda x: (-x[0], x[1]))[:TOP_N]:
                result = simulate(s.closes[i + 1 :], s.closes[i], target, DEFAULT_STOP_PCT, horizon)
                if result is None:
                    continue
                gross, held, reason = result
                exit_day = s.days[i + held]
                bench_gross = (index_by_day[exit_day] / index_by_day[as_of] - 1) * 100
                calendar_days = (exit_day - as_of).days
                trades.append(
                    Trade(
                        symbol=symbol,
                        category=category.value,
                        start_date=as_of,
                        gross_pct=gross,
                        net_pct=self._costs.net(gross, calendar_days),
                        days=held,
                        exit_reason=reason,
                        benchmark_pct=self._costs.net(bench_gross, calendar_days),
                        predicted_prob=prob,
                    )
                )
        v.summary = summarise(trades)
        v.trades = trades
        if probs:
            v.reliability = reliability(outcomes, probs)
            v.ece_pp = ev.expected_calibration_error(outcomes, probs)
            v.coverage = ev.coverage(actual, lows, highs)
        closed = [
            p
            for p in plans
            if p.category is category and p.status is PlanStatus.CLOSED and p.outcome
        ]
        v.journal_closed = len(closed)
        v.journal_outcomes = {o.value: sum(p.outcome is o for p in closed) for o in PlanOutcome}
        return v
