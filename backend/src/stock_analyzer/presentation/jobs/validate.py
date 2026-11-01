"""Job: backtest, calibration and journal review with a go / no-go verdict (``make validate``).

Writes ``var/reports/validation.md``; ``make validate`` copies it to ``docs/reports/``.
"""

import asyncio
import logging
from pathlib import Path

from stock_analyzer.application.use_cases.validation.run_validation import (
    MIN_JOURNAL_PLANS,
    REBALANCE_EVERY,
    TOP_N,
    RunValidation,
    ValidationReport,
)
from stock_analyzer.bootstrap import build_container
from stock_analyzer.domain.validation.backtest import CostModel

logger = logging.getLogger(__name__)
REPORT_NAME = "validation.md"
DATA_NOTE = {
    True: "**synthetic** (mock provider): not evidence of real-world skill",
    False: "real data",
}


def _pct(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:+.{digits}f}%"


def _share(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.0f}%"


def render(report: ValidationReport, costs: CostModel) -> str:
    """Markdown report for docs/reports/validation.md."""
    lines = [
        "# Validation (Phase 5)",
        "",
        f"_Data {report.data_start} … {report.data_end} · {DATA_NOTE[report.is_synthetic]}._",
        "",
        f"Strategy: every {REBALANCE_EVERY} trading days, per holding period, start plans in "
        f"the top {TOP_N} stocks by the predicted chance of the target, using only data known "
        "that day (the live empirical predictor). Exit at the target, the -7% stop or the end "
        "date. "
        f"Net of {costs.round_trip_cost_pct}% costs and tax (STCG {costs.stcg_pct}%, "
        f"LTCG {costs.ltcg_pct}%; no exemption or loss set-off). Benchmark: {report.benchmark}, "
        "same windows, same costs and tax.",
        "",
        "## Verdict (Q70)",
        "",
        "| Holding | Target | Verdict | Why |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {v.category.value} | +{v.target_pct}% | **{v.verdict}** | "
        f"{'; '.join(v.reasons) or 'all criteria met'} |"
        for v in report.categories
    ]
    lines += [
        "",
        "## Backtest",
        "",
        "| Holding | Trades | Win rate | Avg gain | Avg loss | Expectancy (net) | Benchmark "
        "| Avg days | Target hit | Predicted chance |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for v in report.categories:
        s = v.summary
        if s is None:
            lines.append(f"| {v.category.value} | 0 | — | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {v.category.value} | {s.trades} | {_share(s.win_rate)} | {_pct(s.avg_gain_pct)} "
            f"| {_pct(s.avg_loss_pct)} | {_pct(s.expectancy_pct)} "
            f"| {_pct(s.benchmark_expectancy_pct)} | {s.avg_days:.0f} "
            f"| {_share(s.target_hit_rate)} | {_share(s.avg_predicted_prob)} |"
        )
    lines += ["", "## Calibration", ""]
    for v in report.categories:
        lines += [
            f"### {v.category.value} · chance of +{v.target_pct}%",
            "",
            f"ECE {('—' if v.ece_pp is None else f'{v.ece_pp:.1f} pp')} (≤ 5) · "
            f"80% range coverage {_share(v.coverage)} (75-85%)",
            "",
            "| Predicted | Samples | Mean predicted | Happened |",
            "|---|---|---|---|",
        ]
        lines += [
            f"| {r.low * 100:.0f}-{r.high * 100:.0f}% | {r.count} | {_share(r.mean_predicted)} "
            f"| {_share(r.observed)} |"
            for r in v.reliability
        ]
        lines.append("")
    lines += [
        "## Journal",
        "",
        f"Real plans you closed. Below {MIN_JOURNAL_PLANS} closed plans per holding period the "
        "numbers are too few to judge.",
        "",
        "| Holding | Closed | Success | Partial | Failure | Exited early |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {v.category.value} | {v.journal_closed} | {v.journal_outcomes.get('SUCCESS', 0)} "
        f"| {v.journal_outcomes.get('PARTIAL', 0)} | {v.journal_outcomes.get('FAILURE', 0)} "
        f"| {v.journal_outcomes.get('EXITED_EARLY', 0)} |"
        for v in report.categories
    ]
    return "\n".join(lines).rstrip("\n") + "\n"


async def run() -> None:
    """Run the validation and write the report."""
    container = build_container()
    costs = CostModel()
    report = await RunValidation(container.uow_factory, costs).execute()
    path = Path(container.settings.reports_dir) / REPORT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(report, costs))
    for v in report.categories:
        logger.info("%s: %s (%s)", v.category.value, v.verdict, "; ".join(v.reasons))
    logger.info("wrote %s", path)


if __name__ == "__main__":
    asyncio.run(run())
