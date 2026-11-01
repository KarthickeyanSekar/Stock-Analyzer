"""Money and percentage value objects: immutable, ``Decimal`` only, never floats."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Self

from stock_analyzer.domain.shared.percent import round_pct

PAISE = Decimal("0.01")
CURRENCY_CODE_LENGTH = 3  # ISO 4217


def _require_decimal(value: object, what: str) -> None:
    # bool is an int subclass and float loses precision: both are rejected.
    if not isinstance(value, Decimal):
        raise TypeError(f"{what} must be a Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{what} must be finite")


@dataclass(frozen=True, slots=True)
class Money:
    """An amount in one currency (ISO 4217 code, e.g. ``INR``)."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        """Reject floats, NaN/inf and malformed currency codes."""
        _require_decimal(self.amount, "amount")
        if len(self.currency) != CURRENCY_CODE_LENGTH or not self.currency.isupper():
            raise ValueError(f"invalid currency code {self.currency!r}")

    def _same_currency(self, other: "Money") -> None:
        if other.currency != self.currency:
            raise ValueError(f"cannot combine {self.currency} with {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        """Add two amounts in the same currency."""
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two amounts in the same currency."""
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def times(self, factor: Decimal) -> "Money":
        """Multiply by a ``Decimal`` factor (e.g., a quantity)."""
        _require_decimal(factor, "factor")
        return Money(self.amount * factor, self.currency)

    def apply(self, change: "Percentage") -> "Money":
        """Return the amount after a percentage move (``+10%`` of 100 is 110)."""
        return Money(self.amount * (1 + change.points / 100), self.currency)

    def rounded(self) -> "Money":
        """Round to 2 decimal places (paise / cents), half up."""
        return Money(self.amount.quantize(PAISE, rounding=ROUND_HALF_UP), self.currency)

    def change_to(self, other: "Money") -> "Percentage":
        """Percent change from this amount to ``other``."""
        self._same_currency(other)
        if self.amount <= 0:
            raise ValueError("start amount must be positive")
        return Percentage(round_pct((other.amount - self.amount) / self.amount * 100))


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """Percent points: ``Percentage(Decimal("20"))`` means +20%."""

    points: Decimal

    def __post_init__(self) -> None:
        """Reject floats and NaN/inf."""
        _require_decimal(self.points, "points")

    @classmethod
    def of(cls, text: str) -> Self:
        """Build from a string such as ``"9.5"`` (never from a float)."""
        return cls(Decimal(text))

    def __sub__(self, other: "Percentage") -> Decimal:
        """Difference in percentage points (pp)."""
        return self.points - other.points
