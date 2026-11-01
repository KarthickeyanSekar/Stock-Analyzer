"""Admin > Users and invite codes (docs/19-auth-multi-user.md)."""

import uuid
from collections.abc import Sequence
from datetime import timedelta
from uuid import UUID

from stock_analyzer.application.errors import ForbiddenError, NotFoundError
from stock_analyzer.application.ports.auth import AuditEntry
from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.shared.errors import DomainError
from stock_analyzer.domain.users.invite import MAX_USES_LIMIT, InviteCode, generate_code
from stock_analyzer.domain.users.user import Role, User

MAX_VALID_DAYS = 90


class UserAdmin:
    """Invite codes, user list, disable / enable, audit log (admins only)."""

    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        """Use ``clock`` for expiry and audit times."""
        self._uow_factory = uow_factory
        self._clock = clock

    @staticmethod
    def _require_admin(actor: User) -> None:
        if not actor.is_admin:
            raise ForbiddenError("admins only")

    async def create_invite(
        self, actor: User, max_uses: int = 1, valid_days: int = 7, role: Role = Role.USER
    ) -> InviteCode:
        """Create a code (only admins may create admin codes)."""
        self._require_admin(actor)
        if not 1 <= max_uses <= MAX_USES_LIMIT or not 1 <= valid_days <= MAX_VALID_DAYS:
            raise DomainError(f"uses 1-{MAX_USES_LIMIT}, validity 1-{MAX_VALID_DAYS} days")
        now = self._clock.now()
        invite = InviteCode(
            id=uuid.uuid4(),
            code=generate_code(),
            created_by=actor.id,
            role_granted=role,
            max_uses=max_uses,
            expires_at=now + timedelta(days=valid_days),
        )
        async with self._uow_factory() as uow:
            invite = await uow.invites.add(invite)
            await uow.audit.add(
                AuditEntry(now, actor.id, "invite_created", {"code": invite.code, "role": role})
            )
            await uow.commit()
        return invite

    async def invites(self, actor: User) -> list[InviteCode]:
        """Every code, newest first."""
        self._require_admin(actor)
        async with self._uow_factory() as uow:
            return await uow.invites.list_all()

    async def revoke_invite(self, actor: User, invite_id: UUID) -> None:
        """Revoke a code so it can't be used any more."""
        self._require_admin(actor)
        async with self._uow_factory() as uow:
            invite = await uow.invites.get(invite_id)
            if invite is None:
                raise NotFoundError("invite code not found")
            invite.is_revoked = True
            await uow.invites.update(invite)
            await uow.audit.add(
                AuditEntry(self._clock.now(), actor.id, "invite_revoked", {"code": invite.code})
            )
            await uow.commit()

    async def users(self, actor: User) -> list[User]:
        """Every user."""
        self._require_admin(actor)
        async with self._uow_factory() as uow:
            return await uow.users.list_all()

    async def set_disabled(self, actor: User, user_id: UUID, *, disabled: bool) -> User:
        """Disable or enable a user (not yourself); disabling signs them out everywhere."""
        self._require_admin(actor)
        if user_id == actor.id:
            raise ForbiddenError("you can't disable your own account")
        async with self._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if user is None:
                raise NotFoundError("user not found")
            user.is_disabled = disabled
            await uow.users.update(user)
            if disabled:
                await uow.sessions.delete_for_user(user_id)
            await uow.audit.add(
                AuditEntry(
                    self._clock.now(),
                    actor.id,
                    "user_disabled" if disabled else "user_enabled",
                    {"user": str(user_id)},
                )
            )
            await uow.commit()
        return user

    async def audit_log(self, actor: User, limit: int = 100) -> Sequence[AuditEntry]:
        """Newest audit entries."""
        self._require_admin(actor)
        async with self._uow_factory() as uow:
            return await uow.audit.recent(limit)
