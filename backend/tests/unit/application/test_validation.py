import asyncio
import copy
from dataclasses import replace
from datetime import date

from stock_analyzer.application.use_cases.validation.run_validation import RunValidation
from tests.fakes import FakeUnitOfWork, InMemoryStore

CUTOFF = date(2025, 9, 1)


def test_validation_runs_point_in_time_and_is_not_decidable_on_synthetic(
    seeded_store: InMemoryStore,
) -> None:
    store = copy.deepcopy(seeded_store)
    report = asyncio.run(RunValidation(lambda: FakeUnitOfWork(store)).execute())

    assert report.is_synthetic
    assert {v.verdict for v in report.categories} == {"not decidable"}
    d50 = report.categories[0]
    assert d50.summary is not None and d50.summary.trades > 0
    assert d50.ece_pp is not None and d50.coverage is not None

    # Rewrite every price after the cutoff: predictions made before it must not change.
    changed = copy.deepcopy(seeded_store)
    for candles in changed.candles.values():
        for day, c in list(candles.items()):
            if day > CUTOFF:
                candles[day] = replace(
                    c,
                    open=c.open * 2,
                    high=c.high * 2,
                    low=c.low * 2,
                    close=c.close * 2,
                    adj_close=c.adj_close * 2,
                )
    rerun = asyncio.run(RunValidation(lambda: FakeUnitOfWork(changed)).execute())
    before = {
        (t.symbol, t.start_date): t.predicted_prob for t in d50.trades if t.start_date <= CUTOFF
    }
    after = {
        (t.symbol, t.start_date): t.predicted_prob
        for t in rerun.categories[0].trades
        if t.start_date <= CUTOFF
    }
    assert before and before == after
