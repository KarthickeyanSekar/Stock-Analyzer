"""Helpers for percentages stored as percent points (``Decimal("20")`` means +20%)."""

from decimal import ROUND_HALF_UP, Decimal

PCT_PLACES = Decimal("0.0001")


def round_pct(value: Decimal) -> Decimal:
    """Round a percent-point value to 4 decimal places (database precision)."""
    return value.quantize(PCT_PLACES, rounding=ROUND_HALF_UP)


def return_pct(start: Decimal, end: Decimal) -> Decimal:
    """Return the percent change from ``start`` to ``end`` (e.g., 100 → 110 is ``10``)."""
    if start <= 0:
        raise ValueError("start price must be positive")
    return round_pct((end - start) / start * 100)
