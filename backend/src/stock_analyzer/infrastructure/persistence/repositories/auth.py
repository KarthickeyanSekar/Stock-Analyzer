"""SQLAlchemy repositories: accounts, sessions, sign-ins, invites, audit log, watchlists."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.application.ports.auth import AuditEntry, LoginRequest, SessionRecord
from stock_analyzer.domain.users.invite import InviteCode
from stock_analyzer.domain.users.user import Role, User
from stock_analyzer.infrastructure.persistence.models import (
    AuditLogModel,
    InviteCodeModel,
    InviteRedemptionModel,
    JournalSettingsModel,
    LoginRequestModel,
    PlanDailyStatusModel,
    SessionModel,
    TradePlanModel,
    UserModel,
    WatchlistModel,
)


def _user(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        name=row.name,
        provider=row.provider,
        provider_subject=row.provider_subject,
        role=Role(row.role),
        is_disabled=row.is_disabled,
        created_at=row.created_at,
        last_login_at=row.last_login_at,
    )


class SqlAlchemyUserRepository:
    """``users``."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        """Return one user, or ``None``."""
        row = await self._session.get(UserModel, user_id)
        return _user(row) if row else None

    async def by_subject(self, provider: str, subject: str) -> User | None:
        """Find a user by identity-provider subject."""
        row = await self._session.scalar(
            select(UserModel).where(
                UserModel.provider == provider, UserModel.provider_subject == subject
            )
        )
        return _user(row) if row else None

    async def add(self, user: User) -> User:
        """Store a new user."""
        row = UserModel(
            id=user.id,
            email=user.email,
            name=user.name,
            provider=user.provider,
            provider_subject=user.provider_subject,
            role=user.role.value,
            is_disabled=user.is_disabled,
            last_login_at=user.last_login_at,
        )
        self._session.add(row)
        await self._session.flush()
        user.created_at = row.created_at
        return user

    async def update(self, user: User) -> None:
        """Persist role, disabled flag, profile and last sign-in."""
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                email=user.email,
                name=user.name,
                role=user.role.value,
                is_disabled=user.is_disabled,
                last_login_at=user.last_login_at,
            )
        )

    async def list_all(self) -> list[User]:
        """Every user, oldest first."""
        rows = await self._session.scalars(select(UserModel).order_by(UserModel.created_at))
        return [_user(r) for r in rows]

    async def delete(self, user_id: UUID) -> None:
        """Delete the user; plans (and their snapshots), settings, sessions cascade."""
        plan_ids = select(TradePlanModel.id).where(TradePlanModel.user_id == user_id)
        await self._session.execute(
            delete(PlanDailyStatusModel).where(PlanDailyStatusModel.plan_id.in_(plan_ids))
        )
        await self._session.execute(delete(TradePlanModel).where(TradePlanModel.user_id == user_id))
        await self._session.execute(
            delete(JournalSettingsModel).where(JournalSettingsModel.user_id == user_id)
        )
        await self._session.execute(delete(UserModel).where(UserModel.id == user_id))


class SqlAlchemySessionRepository:
    """``sessions`` (token hashes only)."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, record: SessionRecord) -> None:
        """Store a session."""
        self._session.add(
            SessionModel(
                token_hash=record.token_hash, user_id=record.user_id, expires_at=record.expires_at
            )
        )
        await self._session.flush()

    async def get(self, token_hash: str) -> SessionRecord | None:
        """Return a session by token hash."""
        row = await self._session.get(SessionModel, token_hash)
        return SessionRecord(row.token_hash, row.user_id, row.expires_at) if row else None

    async def extend(self, token_hash: str, expires_at: datetime) -> None:
        """Slide the expiry."""
        await self._session.execute(
            update(SessionModel)
            .where(SessionModel.token_hash == token_hash)
            .values(expires_at=expires_at)
        )

    async def delete(self, token_hash: str) -> None:
        """Sign one browser out."""
        await self._session.execute(
            delete(SessionModel).where(SessionModel.token_hash == token_hash)
        )

    async def delete_for_user(self, user_id: UUID) -> None:
        """Sign the user out everywhere."""
        await self._session.execute(delete(SessionModel).where(SessionModel.user_id == user_id))


class SqlAlchemyLoginRequestRepository:
    """``login_requests`` (each state works once)."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, request: LoginRequest) -> None:
        """Store a sign-in in progress."""
        self._session.add(
            LoginRequestModel(
                state=request.state,
                provider=request.provider,
                code_verifier=request.code_verifier,
                nonce=request.nonce,
                invite_code=request.invite_code,
                expires_at=request.expires_at,
            )
        )
        await self._session.flush()

    async def pop(self, state: str) -> LoginRequest | None:
        """Return and delete the request."""
        row = await self._session.get(LoginRequestModel, state)
        if row is None:
            return None
        await self._session.delete(row)
        await self._session.flush()
        return LoginRequest(
            row.state, row.provider, row.code_verifier, row.nonce, row.invite_code, row.expires_at
        )


def _invite(row: InviteCodeModel) -> InviteCode:
    return InviteCode(
        id=row.id,
        code=row.code,
        created_by=row.created_by,
        role_granted=Role(row.role_granted),
        max_uses=row.max_uses,
        expires_at=row.expires_at,
        used_count=row.used_count,
        is_revoked=row.is_revoked,
        created_at=row.created_at,
    )


class SqlAlchemyInviteRepository:
    """``invite_codes`` and ``invite_redemptions``."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, invite: InviteCode) -> InviteCode:
        """Store a new code."""
        row = InviteCodeModel(
            id=invite.id,
            code=invite.code,
            created_by=invite.created_by,
            role_granted=invite.role_granted.value,
            max_uses=invite.max_uses,
            used_count=invite.used_count,
            expires_at=invite.expires_at,
            is_revoked=invite.is_revoked,
        )
        self._session.add(row)
        await self._session.flush()
        invite.created_at = row.created_at
        return invite

    async def by_code(self, code: str) -> InviteCode | None:
        """Find a code."""
        row = await self._session.scalar(
            select(InviteCodeModel).where(InviteCodeModel.code == code)
        )
        return _invite(row) if row else None

    async def get(self, invite_id: UUID) -> InviteCode | None:
        """Find a code by id."""
        row = await self._session.get(InviteCodeModel, invite_id)
        return _invite(row) if row else None

    async def update(self, invite: InviteCode) -> None:
        """Persist uses / revocation."""
        await self._session.execute(
            update(InviteCodeModel)
            .where(InviteCodeModel.id == invite.id)
            .values(used_count=invite.used_count, is_revoked=invite.is_revoked)
        )

    async def list_all(self) -> list[InviteCode]:
        """Every code, newest first."""
        rows = await self._session.scalars(
            select(InviteCodeModel).order_by(InviteCodeModel.created_at.desc())
        )
        return [_invite(r) for r in rows]

    async def add_redemption(self, invite_id: UUID, user_id: UUID, at: datetime) -> None:
        """Record who used a code."""
        self._session.add(
            InviteRedemptionModel(invite_code_id=invite_id, user_id=user_id, redeemed_at=at)
        )
        await self._session.flush()


class SqlAlchemyAuditLog:
    """``audit_log`` (append-only)."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, entry: AuditEntry) -> None:
        """Record an entry."""
        self._session.add(
            AuditLogModel(
                user_id=entry.user_id, action=entry.action, details=entry.details, at=entry.at
            )
        )
        await self._session.flush()

    async def recent(self, limit: int) -> Sequence[AuditEntry]:
        """Newest entries first."""
        rows = await self._session.scalars(
            select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(limit)
        )
        return [AuditEntry(r.at, r.user_id, r.action, dict(r.details)) for r in rows]


class SqlAlchemyWatchlistRepository:
    """``watchlists``."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def list_for(self, user_id: UUID) -> list[int]:
        """Stock ids in the order they were added."""
        rows = await self._session.scalars(
            select(WatchlistModel.stock_id)
            .where(WatchlistModel.user_id == user_id)
            .order_by(WatchlistModel.added_at, WatchlistModel.stock_id)
        )
        return list(rows)

    async def add(self, user_id: UUID, stock_id: int) -> None:
        """Watch a stock (no-op if already watched)."""
        await self._session.execute(
            insert(WatchlistModel)
            .values(user_id=user_id, stock_id=stock_id)
            .on_conflict_do_nothing(index_elements=["user_id", "stock_id"])
        )

    async def remove(self, user_id: UUID, stock_id: int) -> None:
        """Stop watching a stock."""
        await self._session.execute(
            delete(WatchlistModel).where(
                WatchlistModel.user_id == user_id, WatchlistModel.stock_id == stock_id
            )
        )
