"""Sign-in, user admin and watchlist models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from stock_analyzer.domain.users.invite import InviteCode
from stock_analyzer.domain.users.user import Role, User


class ProviderOption(BaseModel):
    """A sign-in button."""

    name: str
    display_name: str


class SignInOptionsResponse(BaseModel):
    """Which sign-in methods are available."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "providers": [{"name": "google", "display_name": "Google"}],
                    "dev_login": True,
                    "dev_accounts": ["admin@stockanalyzer.com"],
                }
            ]
        }
    )

    providers: list[ProviderOption]
    dev_login: bool
    dev_accounts: list[str] = Field(
        default_factory=list, description="One-click dev sign-ins (admin emails); dev only"
    )


class DevLoginBody(BaseModel):
    """Dev-only sign-in."""

    email: str = Field(examples=["dev@example.com"])
    invite_code: str | None = None


class MeResponse(BaseModel):
    """The signed-in user."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "0d6c7b9e-8f0e-4a8e-9d5f-2f1f6c3a9b10",
                    "email": "you@example.com",
                    "name": "You",
                    "role": "admin",
                    "provider": "google",
                    "is_disabled": False,
                    "created_at": "2026-11-01T08:00:00Z",
                    "last_login_at": "2026-11-01T08:00:00Z",
                }
            ]
        }
    )

    id: UUID
    email: str
    name: str
    role: Role
    provider: str
    is_disabled: bool
    created_at: datetime | None
    last_login_at: datetime | None

    @classmethod
    def from_domain(cls, user: User) -> "MeResponse":
        """Map a user."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            provider=user.provider,
            is_disabled=user.is_disabled,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )


class CreateInviteBody(BaseModel):
    """New invite code."""

    max_uses: int = Field(default=1, ge=1, le=100)
    valid_days: int = Field(default=7, ge=1, le=90)
    role: Role = Role.USER


class InviteResponse(BaseModel):
    """An invite code."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "5b8f2c1e-1d0a-4f3b-8a9e-7c6d5e4f3a2b",
                    "code": "SA-7K2M-QX9P",
                    "role_granted": "user",
                    "max_uses": 1,
                    "used_count": 0,
                    "expires_at": "2026-11-08T08:00:00Z",
                    "is_revoked": False,
                    "is_usable": True,
                }
            ]
        }
    )

    id: UUID
    code: str
    role_granted: Role
    max_uses: int
    used_count: int
    expires_at: datetime
    is_revoked: bool
    is_usable: bool

    @classmethod
    def from_domain(cls, invite: InviteCode, now: datetime) -> "InviteResponse":
        """Map an invite code."""
        return cls(
            id=invite.id,
            code=invite.code,
            role_granted=invite.role_granted,
            max_uses=invite.max_uses,
            used_count=invite.used_count,
            expires_at=invite.expires_at,
            is_revoked=invite.is_revoked,
            is_usable=not invite.is_revoked
            and now < invite.expires_at
            and invite.used_count < invite.max_uses,
        )


class SetDisabledBody(BaseModel):
    """Disable or enable a user."""

    is_disabled: bool


class AuditEntryResponse(BaseModel):
    """An audit log entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "at": "2026-11-01T08:00:00Z",
                    "user_id": None,
                    "action": "sign_in",
                    "details": {"provider": "google"},
                }
            ]
        }
    )

    at: datetime
    user_id: UUID | None
    action: str
    details: dict[str, object]
