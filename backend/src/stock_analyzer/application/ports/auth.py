"""Authentication ports (docs/19-auth-multi-user.md; Q71, Q72)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from stock_analyzer.domain.users.invite import InviteCode
from stock_analyzer.domain.users.user import User


@dataclass(frozen=True, slots=True)
class Identity:
    """A verified identity returned by an identity provider."""

    provider: str
    subject: str
    email: str
    name: str


class IdentityProvider(Protocol):
    """An OpenID Connect provider (Google, Microsoft) or a fake one in tests."""

    @property
    def name(self) -> str:
        """Short name used in URLs and stored on the user (``google``)."""
        ...

    @property
    def display_name(self) -> str:
        """Label for the sign-in button."""
        ...

    async def authorization_url(
        self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
    ) -> str:
        """Where to send the browser to sign in (PKCE S256)."""
        ...

    async def exchange(
        self, *, code: str, code_verifier: str, redirect_uri: str, nonce: str
    ) -> Identity:
        """Exchange the code and return the verified identity (raises on any check failing)."""
        ...


@dataclass(frozen=True, slots=True)
class LoginRequest:
    """A sign-in in progress, stored between redirect and callback."""

    state: str
    provider: str
    code_verifier: str
    nonce: str
    invite_code: str | None
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """A signed-in browser (only the token hash is stored)."""

    token_hash: str
    user_id: UUID
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Something security-relevant that happened."""

    at: datetime
    user_id: UUID | None
    action: str
    details: dict[str, Any]


class UserRepository(Protocol):
    """User accounts."""

    async def get(self, user_id: UUID) -> User | None:
        """Return one user, or ``None``."""
        ...

    async def by_subject(self, provider: str, subject: str) -> User | None:
        """Find a user by identity-provider subject."""
        ...

    async def add(self, user: User) -> User:
        """Store a new user."""
        ...

    async def update(self, user: User) -> None:
        """Persist changes (role, disabled, last sign-in)."""
        ...

    async def list_all(self) -> list[User]:
        """Every user, oldest first."""
        ...

    async def delete(self, user_id: UUID) -> None:
        """Delete the user and everything they own."""
        ...


class SessionRepository(Protocol):
    """Signed-in browsers."""

    async def add(self, record: SessionRecord) -> None:
        """Store a session."""
        ...

    async def get(self, token_hash: str) -> SessionRecord | None:
        """Return a session by token hash."""
        ...

    async def extend(self, token_hash: str, expires_at: datetime) -> None:
        """Slide the expiry."""
        ...

    async def delete(self, token_hash: str) -> None:
        """Sign one browser out."""
        ...

    async def delete_for_user(self, user_id: UUID) -> None:
        """Sign the user out everywhere."""
        ...


class LoginRequestRepository(Protocol):
    """Sign-ins in progress (state, PKCE verifier, nonce)."""

    async def add(self, request: LoginRequest) -> None:
        """Store a sign-in in progress."""
        ...

    async def pop(self, state: str) -> LoginRequest | None:
        """Return and delete it (each state works once)."""
        ...


class InviteRepository(Protocol):
    """Invite codes and who used them."""

    async def add(self, invite: InviteCode) -> InviteCode:
        """Store a new code."""
        ...

    async def by_code(self, code: str) -> InviteCode | None:
        """Find a code."""
        ...

    async def get(self, invite_id: UUID) -> InviteCode | None:
        """Find a code by id."""
        ...

    async def update(self, invite: InviteCode) -> None:
        """Persist uses / revocation."""
        ...

    async def list_all(self) -> list[InviteCode]:
        """Every code, newest first."""
        ...

    async def add_redemption(self, invite_id: UUID, user_id: UUID, at: datetime) -> None:
        """Record who used a code."""
        ...


class AuditLog(Protocol):
    """Append-only audit log."""

    async def add(self, entry: AuditEntry) -> None:
        """Record an entry."""
        ...

    async def recent(self, limit: int) -> Sequence[AuditEntry]:
        """Newest entries first."""
        ...


class WatchlistRepository(Protocol):
    """Stocks a user watches."""

    async def list_for(self, user_id: UUID) -> list[int]:
        """Stock ids, in the order they were added."""
        ...

    async def add(self, user_id: UUID, stock_id: int) -> None:
        """Watch a stock (no-op if already watched)."""
        ...

    async def remove(self, user_id: UUID, stock_id: int) -> None:
        """Stop watching a stock."""
        ...
