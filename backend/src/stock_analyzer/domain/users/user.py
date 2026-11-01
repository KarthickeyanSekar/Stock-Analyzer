"""User accounts and roles."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    """What a user may do: admins also manage users, invites and data providers."""

    ADMIN = "admin"
    USER = "user"


@dataclass(slots=True)
class User:
    """A person signed in through an identity provider (Google, Microsoft, dev)."""

    id: UUID
    email: str
    name: str
    provider: str
    provider_subject: str
    role: Role = Role.USER
    is_disabled: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None

    @property
    def is_admin(self) -> bool:
        """Whether the user has the admin role."""
        return self.role is Role.ADMIN
