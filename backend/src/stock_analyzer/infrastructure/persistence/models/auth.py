"""User accounts, sessions, invites, audit log and watchlists (docs/19-auth-multi-user.md)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.infrastructure.persistence.models.base import Base

ROLES_SQL = "('admin', 'user')"


class UserModel(Base):
    """A person, identified by their identity provider's subject id."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject"),
        CheckConstraint(f"role IN {ROLES_SQL}", name="role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320))
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(32))
    provider_subject: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(8), server_default="user")
    is_disabled: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SessionModel(Base):
    """A signed-in browser; only the SHA-256 of the cookie token is stored (Q71)."""

    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginRequestModel(Base):
    """A sign-in between the redirect and the callback (state, PKCE verifier, nonce)."""

    __tablename__ = "login_requests"

    state: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    code_verifier: Mapped[str] = mapped_column(String(128))
    nonce: Mapped[str] = mapped_column(String(64))
    invite_code: Mapped[str | None] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class InviteCodeModel(Base):
    """A shareable sign-up code."""

    __tablename__ = "invite_codes"
    __table_args__ = (
        CheckConstraint(f"role_granted IN {ROLES_SQL}", name="role_granted"),
        CheckConstraint("max_uses >= 1 AND used_count >= 0", name="uses"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    role_granted: Mapped[str] = mapped_column(String(8), server_default="user")
    max_uses: Mapped[int] = mapped_column(Integer, server_default="1")
    used_count: Mapped[int] = mapped_column(Integer, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteRedemptionModel(Base):
    """Who used which invite code."""

    __tablename__ = "invite_redemptions"

    invite_code_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invite_codes.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditLogModel(Base):
    """Append-only log of security-relevant actions (kept when a user is deleted)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WatchlistModel(Base):
    """A stock on a user's watchlist."""

    __tablename__ = "watchlists"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
