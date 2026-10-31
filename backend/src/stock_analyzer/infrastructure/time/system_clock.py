"""Clock adapter backed by the system clock."""

from datetime import UTC, datetime


class SystemClock:
    """Return the real current time in UTC."""

    def now(self) -> datetime:
        """Return the current UTC time."""
        return datetime.now(tz=UTC)
