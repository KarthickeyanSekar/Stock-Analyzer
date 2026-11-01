"""Fundamentals provider port: implemented by the mock plugin now, real APIs later."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals


class FundamentalsProvider(Protocol):
    """Source of quarterly results for the instruments of one market."""

    @property
    def name(self) -> str:
        """Plugin name stored as ``source_provider`` on every record (e.g., ``mock``)."""
        ...

    def quarterly_fundamentals(
        self, symbol: str, start: date, end: date
    ) -> Sequence[QuarterlyFundamentals]:
        """Return quarters ending in ``start``..``end`` that were announced by ``end``."""
        ...
