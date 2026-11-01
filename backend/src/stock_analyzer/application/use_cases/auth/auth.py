"""Sign-in, sessions and account deletion (docs/19-auth-multi-user.md; Q71-Q73).

OIDC Authorization Code + PKCE: the browser is sent to the provider with ``state``, ``nonce``
and an S256 ``code_challenge``; the callback must present the same state (once, within ten
minutes) and the provider adapter verifies the ID token. Session tokens are random, only their
SHA-256 is stored, and they slide forward while used.
"""

import base64
import hashlib
import secrets
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta

from stock_analyzer.application.errors import AuthError
from stock_analyzer.application.ports.auth import (
    AuditEntry,
    Identity,
    IdentityProvider,
    LoginRequest,
    SessionRecord,
)
from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.application.ports.repositories import UnitOfWork, UnitOfWorkFactory
from stock_analyzer.domain.users.invite import InvalidInviteError, normalise
from stock_analyzer.domain.users.user import Role, User

SESSION_LIFETIME = timedelta(days=7)
SESSION_REFRESH_AFTER = timedelta(days=1)  # slide the expiry at most once a day per session
LOGIN_REQUEST_LIFETIME = timedelta(minutes=10)
DEV_PROVIDER = "dev"


def hash_token(token: str) -> str:
    """SHA-256 of a session token (what is stored)."""
    return hashlib.sha256(token.encode()).hexdigest()


def code_challenge(verifier: str) -> str:
    """PKCE S256: base64url(sha256(verifier)) without padding."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@dataclass(frozen=True, slots=True)
class SignedIn:
    """A new session: the raw token goes into the cookie and nowhere else."""

    token: str
    user: User


class AuthService:
    """Sign users in and out; resolve the session cookie to a user."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        providers: Mapping[str, IdentityProvider],
        clock: Clock,
        admin_emails: frozenset[str],
        *,
        dev_login_enabled: bool = False,
    ) -> None:
        """Use ``providers`` (name → provider); ``admin_emails`` become admins on first sign-in."""
        self._uow_factory = uow_factory
        self._providers = providers
        self._clock = clock
        self._admin_emails = frozenset(e.lower() for e in admin_emails)
        self._dev_login_enabled = dev_login_enabled

    @property
    def is_dev_login_enabled(self) -> bool:
        """Whether the dev-only sign-in is available (never in prod)."""
        return self._dev_login_enabled

    def providers(self) -> list[tuple[str, str]]:
        """``(name, display name)`` of each configured provider."""
        return [(p.name, p.display_name) for p in self._providers.values()]

    async def start(self, provider: str, redirect_uri: str, invite_code: str | None) -> str:
        """Begin a sign-in and return the provider URL to redirect to."""
        idp = self._providers.get(provider)
        if idp is None:
            raise AuthError(f"sign-in with {provider} is not configured")
        request = LoginRequest(
            state=secrets.token_urlsafe(32),
            provider=provider,
            code_verifier=secrets.token_urlsafe(64),
            nonce=secrets.token_urlsafe(32),
            invite_code=normalise(invite_code) if invite_code else None,
            expires_at=self._clock.now() + LOGIN_REQUEST_LIFETIME,
        )
        async with self._uow_factory() as uow:
            await uow.login_requests.add(request)
            await uow.commit()
        return await idp.authorization_url(
            state=request.state,
            nonce=request.nonce,
            code_challenge=code_challenge(request.code_verifier),
            redirect_uri=redirect_uri,
        )

    async def finish(self, provider: str, state: str, code: str, redirect_uri: str) -> SignedIn:
        """Complete a sign-in from the provider callback."""
        async with self._uow_factory() as uow:
            request = await uow.login_requests.pop(state)
            await uow.commit()
        if request is None or request.provider != provider:
            raise AuthError("this sign-in link is not valid any more; please start again")
        if self._clock.now() >= request.expires_at:
            raise AuthError("the sign-in took too long; please start again")
        identity = await self._providers[provider].exchange(
            code=code,
            code_verifier=request.code_verifier,
            redirect_uri=redirect_uri,
            nonce=request.nonce,
        )
        return await self._sign_in(identity, request.invite_code)

    async def dev_login(self, email: str, invite_code: str | None = None) -> SignedIn:
        """Sign in without a provider (local development only)."""
        if not self._dev_login_enabled:
            raise AuthError("dev sign-in is disabled")
        email = email.strip().lower()
        if "@" not in email:
            raise AuthError("enter an email address")
        identity = Identity(DEV_PROVIDER, email, email, email.split("@")[0])
        return await self._sign_in(identity, normalise(invite_code) if invite_code else None)

    async def _sign_in(self, identity: Identity, invite_code: str | None) -> SignedIn:
        now = self._clock.now()
        async with self._uow_factory() as uow:
            user = await uow.users.by_subject(identity.provider, identity.subject)
            if user is None:
                user = await self._sign_up(uow, identity, invite_code)
            elif user.is_disabled:
                raise AuthError("this account is disabled; ask an admin")
            user.last_login_at = now
            user.email, user.name = identity.email, identity.name or user.name
            await uow.users.update(user)
            if user.is_admin:  # Q73: data from before accounts goes to the first admin
                await uow.trade_plans.claim_unowned(user.id)
                await uow.settings.claim_unowned(user.id)
            token = secrets.token_urlsafe(32)
            await uow.sessions.add(
                SessionRecord(hash_token(token), user.id, now + SESSION_LIFETIME)
            )
            await uow.audit.add(
                AuditEntry(now, user.id, "sign_in", {"provider": identity.provider})
            )
            await uow.commit()
        return SignedIn(token, user)

    async def _sign_up(self, uow: UnitOfWork, identity: Identity, invite_code: str | None) -> User:
        now = self._clock.now()
        is_admin_email = identity.email.lower() in self._admin_emails
        invite = None
        if not is_admin_email:
            if not invite_code:
                raise AuthError("you need an invite code to create an account")
            invite = await uow.invites.by_code(invite_code)
            if invite is None:
                raise AuthError("this invite code does not exist")
            try:
                invite.redeem(now)
            except InvalidInviteError as error:
                raise AuthError(str(error)) from error
        user = User(
            id=uuid.uuid4(),
            email=identity.email,
            name=identity.name or identity.email,
            provider=identity.provider,
            provider_subject=identity.subject,
            role=Role.ADMIN if is_admin_email else (invite.role_granted if invite else Role.USER),
        )
        await uow.users.add(user)
        if invite is not None:
            await uow.invites.update(invite)
            await uow.invites.add_redemption(invite.id, user.id, now)
        await uow.audit.add(
            AuditEntry(
                now,
                user.id,
                "sign_up",
                {"role": user.role.value, "invite": invite.code if invite else None},
            )
        )
        return user

    async def current_user(self, token: str | None) -> User | None:
        """Resolve a session cookie; expired sessions and disabled users get ``None``."""
        if not token:
            return None
        now = self._clock.now()
        token_hash = hash_token(token)
        async with self._uow_factory() as uow:
            session = await uow.sessions.get(token_hash)
            if session is None:
                return None
            if now >= session.expires_at:
                await uow.sessions.delete(token_hash)
                await uow.commit()
                return None
            user = await uow.users.get(session.user_id)
            if user is None or user.is_disabled:
                return None
            if session.expires_at - now < SESSION_LIFETIME - SESSION_REFRESH_AFTER:
                await uow.sessions.extend(token_hash, now + SESSION_LIFETIME)
                await uow.commit()
        return user

    async def sign_out(self, token: str) -> None:
        """End this browser's session."""
        async with self._uow_factory() as uow:
            await uow.sessions.delete(hash_token(token))
            await uow.commit()

    async def delete_account(self, user: User) -> None:
        """Delete the user and everything they own; the audit entry keeps no personal data."""
        async with self._uow_factory() as uow:
            await uow.sessions.delete_for_user(user.id)
            await uow.users.delete(user.id)
            await uow.audit.add(AuditEntry(self._clock.now(), None, "account_deleted", {}))
            await uow.commit()
