"""Clock port, so use cases never call ``datetime.now`` directly."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current, timezone-aware time."""

    def now(self) -> datetime:
        """Return the current time as a timezone-aware datetime."""
        ...
