from datetime import date
from decimal import Decimal

import pytest

from stock_analyzer.domain.journal.trade_plan import (
    InvalidExitDateError,
    InvalidPlanError,
    PlanAlreadyClosedError,
    PlanOutcome,
    PlanStatus,
    TradePlan,
    evaluate_outcome,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory

START = date(2026, 1, 5)
END = date(2026, 2, 24)


def make_plan(**overrides: object) -> TradePlan:
    values: dict[str, object] = {
        "stock_id": 1,
        "category": HoldingCategory.D50,
        "start_date": START,
        "planned_end_date": END,
        "entry_price": Decimal("100"),
        "target_pct": Decimal("10"),
    }
    values.update(overrides)
    return TradePlan.start(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("10", PlanOutcome.SUCCESS),
        ("9.5", PlanOutcome.SUCCESS),  # lower edge of ±0.5 pp
        ("10.5", PlanOutcome.SUCCESS),  # upper edge of ±0.5 pp
        ("10.6", PlanOutcome.PARTIAL),  # above: model too cautious, tuning required
        ("15", PlanOutcome.PARTIAL),
        ("11", PlanOutcome.PARTIAL),
        ("9.4", PlanOutcome.FAILURE),  # below: prediction failed
        ("-5", PlanOutcome.FAILURE),
    ],
)
def test_outcome_compares_actual_with_prediction_within_tolerance(
    actual: str, expected: PlanOutcome
) -> None:
    assert evaluate_outcome(Decimal(actual), Decimal("10"), Decimal("0.5")) is expected


def test_new_plan_is_active_with_default_tolerance_and_stop() -> None:
    plan = make_plan()

    assert plan.status is PlanStatus.ACTIVE
    assert plan.success_tolerance_pp == Decimal("0.5")
    assert plan.stop_pct == Decimal("-7")
    assert plan.target_price == Decimal("110")
    assert plan.stop_price == Decimal("93")


def test_close_calculates_return_and_outcome() -> None:
    plan = make_plan()

    outcome = plan.close(date(2026, 2, 20), Decimal("110.2"))

    assert outcome is PlanOutcome.SUCCESS
    assert plan.actual_return_pct == Decimal("10.2000")
    assert plan.status is PlanStatus.CLOSED


def test_close_uses_the_tolerance_locked_at_start() -> None:
    plan = make_plan(success_tolerance_pp=Decimal("2"))

    assert plan.close(date(2026, 2, 20), Decimal("111.5")) is PlanOutcome.SUCCESS


def test_exiting_early_is_recorded_as_exited_early() -> None:
    plan = make_plan()

    assert plan.close(date(2026, 1, 20), Decimal("120"), exited_early=True) is (
        PlanOutcome.EXITED_EARLY
    )


def test_a_plan_cannot_be_closed_twice() -> None:
    plan = make_plan()
    plan.close(date(2026, 2, 20), Decimal("110"))

    with pytest.raises(PlanAlreadyClosedError):
        plan.close(date(2026, 2, 21), Decimal("111"))


def test_exit_before_start_is_rejected() -> None:
    with pytest.raises(InvalidExitDateError):
        make_plan().close(date(2026, 1, 1), Decimal("110"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"entry_price": Decimal("0")},
        {"target_pct": Decimal("0")},
        {"stop_pct": Decimal("1")},
        {"success_tolerance_pp": Decimal("-0.1")},
        {"planned_end_date": START},
    ],
)
def test_invalid_plans_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(InvalidPlanError):
        make_plan(**overrides)
