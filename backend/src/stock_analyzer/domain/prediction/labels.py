"""Training labels: what really happened after a date (docs/26-ml-pipeline.md §3).

Triple barrier per target: the upper barrier is the target, the lower barrier the stop-loss and
the vertical barrier the holding period. A label at ``t`` uses only prices **after** ``t``, and
there is no label when the holding period runs past the end of the data.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from stock_analyzer.domain.prediction.prediction import TARGET_PCTS

DEFAULT_STOP_PCT = -7.0


@dataclass(frozen=True, slots=True)
class Label:
    """Outcome of holding from one date for one holding period."""

    forward_return_pct: float
    is_stopped: bool  # the stop-loss was touched before the end
    hits: dict[int, bool]  # target % → reached before the stop

    def first_barrier(self, target_pct: int) -> str:
        """Which barrier came first for ``target_pct``: TARGET, STOP or TIME."""
        if self.hits[target_pct]:
            return "TARGET"
        return "STOP" if self.is_stopped else "TIME"


def make_label(
    future_closes: Sequence[float],
    entry: float,
    horizon: int,
    stop_pct: float = DEFAULT_STOP_PCT,
) -> Label | None:
    """Label the holding period starting at ``entry`` from the next ``horizon`` closes.

    Args:
        future_closes: Adjusted closes strictly after the label date, in order.
        entry: Adjusted close on the label date.
        horizon: Holding period in trading days.
        stop_pct: Stop-loss in percent points (negative).
    """
    if horizon <= 0 or len(future_closes) < horizon or entry <= 0:
        return None
    window = future_closes[:horizon]
    stop_ratio = 1 + stop_pct / 100
    best, stopped = 1.0, False
    for price in window:
        ratio = price / entry
        if ratio <= stop_ratio:
            stopped = True
            break
        best = max(best, ratio)
    return Label(
        forward_return_pct=(window[-1] / entry - 1) * 100,
        is_stopped=stopped,
        hits={target: best >= 1 + target / 100 for target in TARGET_PCTS},
    )
