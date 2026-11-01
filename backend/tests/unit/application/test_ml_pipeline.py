import asyncio
import copy
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from stock_analyzer.application.use_cases.ml.build_features import BuildFeaturesAndLabels
from stock_analyzer.application.use_cases.ml.rollback_model import RollbackModel
from stock_analyzer.application.use_cases.ml.run_predictions import RunPredictions
from stock_analyzer.application.use_cases.ml.train_models import TrainHoldingPeriodModels
from stock_analyzer.domain.analysis.features import FEATURE_SET_VERSION
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction import evaluation
from stock_analyzer.domain.prediction.evaluation import GateReport
from stock_analyzer.domain.prediction.model_version import ModelStatus
from stock_analyzer.infrastructure.ml.lightgbm_trainer import LightGbmTrainer
from tests.fakes import FakeUnitOfWork, InMemoryStore

CUTOFF = date(2025, 6, 2)


class Clock:
    def __init__(self) -> None:
        self.t = datetime(2026, 11, 1, tzinfo=UTC)

    def now(self) -> datetime:
        self.t = self.t.replace(second=(self.t.second + 1) % 60, minute=self.t.minute + 1)
        return self.t


@pytest.fixture(scope="module")
def built(seeded_store: InMemoryStore) -> InMemoryStore:
    store = copy.deepcopy(seeded_store)
    asyncio.run(BuildFeaturesAndLabels(lambda: FakeUnitOfWork(store)).execute())
    return store


def test_build_is_idempotent_and_labels_stop_before_the_data_end(
    built: InMemoryStore,
) -> None:
    before = (len(built.features), len(built.labels))
    asyncio.run(BuildFeaturesAndLabels(lambda: FakeUnitOfWork(built)).execute())

    assert (len(built.features), len(built.labels)) == before
    last_day = max(d for (_, _, d) in built.features)
    assert not [k for k in built.labels if k[2] == last_day]  # nothing to learn from yet
    label_days = {d for (c, _, d) in built.labels if c == "1Y"}
    assert max(label_days) < last_day


def test_features_ignore_future_prices_and_labels_use_them(
    seeded_store: InMemoryStore, built: InMemoryStore
) -> None:
    changed = copy.deepcopy(seeded_store)
    for candles in changed.candles.values():
        for day, c in list(candles.items()):
            if day > CUTOFF:  # rewrite the future: double every later price
                candles[day] = replace(
                    c,
                    open=c.open * 2,
                    high=c.high * 2,
                    low=c.low * 2,
                    close=c.close * 2,
                    adj_close=c.adj_close * 2,
                )
    asyncio.run(BuildFeaturesAndLabels(lambda: FakeUnitOfWork(changed)).execute())

    past = {k: v for k, v in built.features.items() if k[2] <= CUTOFF}
    assert past
    assert all(changed.features[k] == v for k, v in past.items())
    # A 50D label dated a few weeks before the cutoff ends after it: its outcome must change.
    crossing = next(
        k for k in built.labels if k[0] == "50D" and CUTOFF - timedelta(days=30) < k[2] < CUTOFF
    )
    finished = next(
        k for k in built.labels if k[0] == "50D" and k[2] < CUTOFF - timedelta(days=120)
    )
    assert changed.labels[crossing] != built.labels[crossing]
    assert changed.labels[finished] == built.labels[finished]


def test_training_registers_the_candidate_with_its_gate_report(
    built: InMemoryStore, tmp_path: Path
) -> None:
    store = copy.deepcopy(built)
    results = asyncio.run(
        TrainHoldingPeriodModels(
            lambda: FakeUnitOfWork(store),
            LightGbmTrainer(rounds=30),
            Clock(),
            str(tmp_path),
            "abc123",
        ).execute([HoldingCategory.D50, HoldingCategory.Y3])
    )

    d50, y3 = results
    assert d50.version is not None and d50.folds
    assert d50.version.metrics["gates"]["checks"] == d50.gates.checks
    assert d50.version.params["code_version"] == "abc123"
    assert d50.version.feature_set == FEATURE_SET_VERSION
    assert (tmp_path / (d50.version.artifact_path or "")).exists()
    assert (d50.version.status is ModelStatus.ACTIVE) is d50.gates.passed
    assert y3.version is None and not y3.gates.passed  # 2 years of data: no 3Y fold


def test_only_passing_models_activate_and_rollback_restores(
    built: InMemoryStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = copy.deepcopy(built)
    passed = GateReport(checks={"all": True})
    monkeypatch.setattr(evaluation, "evaluate_gates", lambda *_args: passed)
    train = TrainHoldingPeriodModels(
        lambda: FakeUnitOfWork(store), LightGbmTrainer(rounds=10), Clock(), str(tmp_path)
    )

    first = asyncio.run(train.execute([HoldingCategory.D50]))[0].version
    second = asyncio.run(train.execute([HoldingCategory.D50]))[0].version
    assert first and second
    assert (first.status, second.status) == (ModelStatus.RETIRED, ModelStatus.ACTIVE)

    restored = asyncio.run(
        RollbackModel(lambda: FakeUnitOfWork(store), Clock()).execute(HoldingCategory.D50)
    )
    assert restored.id == first.id
    assert (first.status, second.status) == (ModelStatus.ACTIVE, ModelStatus.RETIRED)

    failed = GateReport(checks={"beats_baselines": False})
    monkeypatch.setattr(evaluation, "evaluate_gates", lambda *_args: failed)
    third = asyncio.run(train.execute([HoldingCategory.D50]))[0].version
    assert third and third.status is ModelStatus.CANDIDATE
    assert first.status is ModelStatus.ACTIVE  # a failing candidate never replaces it


def test_predictions_use_the_active_model_and_fall_back_to_the_baseline(
    built: InMemoryStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = copy.deepcopy(built)
    monkeypatch.setattr(
        evaluation, "evaluate_gates", lambda *_args: GateReport(checks={"all": True})
    )
    trainer = LightGbmTrainer(rounds=10)
    version = asyncio.run(
        TrainHoldingPeriodModels(
            lambda: FakeUnitOfWork(store), trainer, Clock(), str(tmp_path)
        ).execute([HoldingCategory.D50])
    )[0].version
    assert version is not None

    run = asyncio.run(
        RunPredictions(lambda: FakeUnitOfWork(store), trainer, str(tmp_path)).execute()
    )

    assert run.ml == len(store.stocks)
    assert run.baseline > 0
    latest = max(p.as_of for p in store.predictions.values())
    todays = [p for p in store.predictions.values() if p.as_of == latest]
    ml = [p for p in todays if p.model_version == version.name]
    assert {p.category for p in ml} == {HoldingCategory.D50}
    for p in ml:
        assert p.range.p10_pct <= p.range.p50_pct <= p.range.p90_pct
        hits = [p.prob_hit[t] for t in sorted(p.prob_hit)]
        assert hits == sorted(hits, reverse=True)
        assert all(isinstance(v, Decimal) for v in hits)
