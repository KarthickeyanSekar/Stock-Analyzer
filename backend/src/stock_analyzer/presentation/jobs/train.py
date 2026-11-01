"""Job: train, evaluate and gate ML models per category; write the evaluation report.

``make train`` runs it and copies the report to ``docs/reports/model-evaluation.md``.
"""

import asyncio
import logging
from pathlib import Path

from stock_analyzer.application.use_cases.ml.train_models import (
    CategoryResult,
    TrainHoldingPeriodModels,
)
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)
REPORT_NAME = "model-evaluation.md"
FOLD_HEADER = (
    "| Test period | Samples | Pinball (model / universe / momentum) "
    "| Coverage | ECE pp | Direction |"
)


def render_report(results: list[CategoryResult], data_note: str) -> str:
    """Markdown evaluation report: gates and walk-forward scores per category."""
    lines = [
        "# Model evaluation (walk-forward)",
        "",
        f"_{data_note}_",
        "",
        "Pinball loss: lower is better (average over p10/p50/p90). Coverage: share of outcomes",
        "inside the 80% range (target 75-85%). ECE: calibration error of the probabilities in",
        "percentage points (≤ 5). A model becomes ACTIVE only when every gate passes (Q51).",
        "",
        "| Category | Samples | Folds | Pinball (model / universe / momentum) | Coverage | ECE pp "
        "| Direction | Gates | Result |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        d = r.gates.details
        failed = [name for name, ok in r.gates.checks.items() if not ok]
        outcome = (
            "✅ ACTIVE"
            if r.activated
            else ("kept current / baseline" if r.version else "not trained (too little data)")
        )
        lines.append(
            f"| {r.category.value} | {r.samples} | {len(r.folds)} | "
            f"{d.get('pinball', '—')} / {d.get('pinball_universe', '—')} / "
            f"{d.get('pinball_momentum', '—')} | {d.get('coverage', '—')} | {d.get('ece_pp', '—')} "
            f"| {d.get('direction_accuracy', '—')} | "
            f"{'all passed' if r.gates.passed else 'failed: ' + ', '.join(failed)} | {outcome} |"
        )
    lines += ["", "## Folds", ""]
    for r in results:
        if not r.folds:
            continue
        lines += [
            f"### {r.category.value}",
            "",
            FOLD_HEADER,
            "|---|---|---|---|---|---|",
        ]
        lines += [
            f"| {f['test_start']} … {f['test_end']} | {f['samples']} | {f['pinball']} / "
            f"{f['pinball_universe']} / {f['pinball_momentum']} | {f['coverage']} | "
            f"{f['ece_pp']} | {f['direction_accuracy']} |"
            for f in r.folds
        ]
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


async def run() -> None:
    """Train every category and write the report."""
    container = build_container()
    settings = container.settings
    results = await TrainHoldingPeriodModels(
        container.uow_factory,
        container.trainer,
        container.clock,
        settings.models_dir,
        settings.code_version,
    ).execute()
    for r in results:
        logger.info(
            "%s: %d samples, gates %s, %s",
            r.category.value,
            r.samples,
            "passed" if r.gates.passed else "failed",
            "ACTIVE" if r.activated else "not activated",
        )
    report = Path(settings.reports_dir) / REPORT_NAME
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        render_report(results, "Synthetic data (mock provider): not evidence of real-world skill.")
    )
    logger.info("wrote %s", report)


if __name__ == "__main__":
    asyncio.run(run())
