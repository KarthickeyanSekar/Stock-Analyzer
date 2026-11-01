"""Invite codes: who may sign up (docs/19-auth-multi-user.md "Invite codes")."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from stock_analyzer.domain.shared.errors import DomainError
from stock_analyzer.domain.users.user import Role

DEFAULT_VALID_FOR = timedelta(days=7)
# No 0/O or 1/I, so codes read out loud or typed from a phone are unambiguous.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_USES_LIMIT = 100


class InvalidInviteError(DomainError):
    """Raised when an invite code can't be used; the message is safe to show."""


def generate_code(choice: Callable[[str], str] = secrets.choice) -> str:
    """A code like ``SA-7K2M-QX9P`` (8 random characters, ~40 bits)."""
    first, second = ("".join(choice(CODE_ALPHABET) for _ in range(4)) for _ in range(2))
    return f"SA-{first}-{second}"


def normalise(code: str) -> str:
    """Accept lower case and stray spaces from a pasted code."""
    return code.strip().upper()


@dataclass(slots=True)
class InviteCode:
    """A shareable code that lets someone create an account."""

    id: UUID
    code: str
    created_by: UUID | None
    role_granted: Role
    max_uses: int
    expires_at: datetime
    used_count: int = 0
    is_revoked: bool = False
    created_at: datetime | None = None

    def check(self, now: datetime) -> None:
        """Raise :class:`InvalidInviteError` unless the code can be used right now."""
        if self.is_revoked:
            raise InvalidInviteError("this invite code was revoked")
        if now >= self.expires_at:
            raise InvalidInviteError("this invite code has expired")
        if self.used_count >= self.max_uses:
            raise InvalidInviteError("this invite code has already been used")

    def redeem(self, now: datetime) -> None:
        """Use the code once (after :meth:`check`)."""
        self.check(now)
        self.used_count += 1
