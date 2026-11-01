import asyncio
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from joserfc import jwt
from joserfc.jwk import RSAKey

from stock_analyzer.application.errors import AuthError
from stock_analyzer.application.use_cases.auth.auth import AuthService, code_challenge
from stock_analyzer.infrastructure.auth.oidc import OidcIdentityProvider
from stock_analyzer.infrastructure.config.settings import Environment, Settings
from tests.fakes import FakeUnitOfWork, InMemoryStore

ISSUER = "https://idp.example"
CLIENT_ID = "client-123"
KEY = RSAKey.generate_key(2048, parameters={"kid": "k1"})
OTHER_KEY = RSAKey.generate_key(2048, parameters={"kid": "k1"})


def id_token(nonce: str, key: RSAKey = KEY, **claims: Any) -> str:
    now = int(time.time())
    payload = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "sub": "user-1",
        "email": "Person@Example.com",
        "email_verified": True,
        "name": "A Person",
        "nonce": nonce,
        "iat": now,
        "exp": now + 300,
    } | claims
    return jwt.encode({"alg": "RS256", "kid": "k1"}, payload, key)


class FakeIdp:
    """Serves discovery, JWKS and a token endpoint; records the token request."""

    def __init__(self, token: str, issuer: str = ISSUER) -> None:
        self.token = token
        self.issuer = issuer
        self.token_form: dict[str, list[str]] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": self.issuer,
                    "authorization_endpoint": "https://idp.example/authorize",
                    "token_endpoint": "https://idp.example/token",
                    "jwks_uri": "https://idp.example/jwks",
                },
            )
        if request.url.path == "/jwks":
            return httpx.Response(200, json={"keys": [KEY.as_dict(private=False)]})
        if request.url.path == "/token":
            self.token_form = parse_qs(request.content.decode())
            return httpx.Response(200, json={"id_token": self.token})
        return httpx.Response(404)


def provider(idp: FakeIdp) -> OidcIdentityProvider:
    return OidcIdentityProvider(
        name="google",
        display_name="Google",
        discovery_url="https://idp.example/.well-known/openid-configuration",
        client_id=CLIENT_ID,
        client_secret="secret",  # noqa: S106 - fake client secret for the fake provider
        client=httpx.AsyncClient(transport=httpx.MockTransport(idp)),
    )


def exchange(idp: FakeIdp, nonce: str = "n-1") -> object:
    return asyncio.run(
        provider(idp).exchange(
            code="c", code_verifier="v", redirect_uri="https://app/cb", nonce=nonce
        )
    )


def test_authorization_url_uses_pkce_state_and_nonce() -> None:
    url = asyncio.run(
        provider(FakeIdp("")).authorization_url(
            state="s-1", nonce="n-1", code_challenge="cc", redirect_uri="https://app/cb"
        )
    )
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://idp.example/authorize?")
    assert query["code_challenge_method"] == ["S256"]
    assert (query["state"], query["nonce"], query["code_challenge"]) == (["s-1"], ["n-1"], ["cc"])
    assert query["scope"] == ["openid email profile"]


def test_a_valid_token_gives_the_identity_and_sends_the_verifier() -> None:
    idp = FakeIdp(id_token("n-1"))
    identity = exchange(idp)

    assert identity.subject == "user-1" and identity.email == "person@example.com"  # type: ignore[attr-defined]
    assert idp.token_form["code_verifier"] == ["v"]


@pytest.mark.parametrize(
    "token",
    [
        id_token("n-1", key=OTHER_KEY),  # forged signature
        id_token("n-1", aud="someone-else"),
        id_token("n-1", iss="https://evil.example"),
        id_token("other-nonce"),  # replayed / mixed-up sign-in
        id_token("n-1", exp=int(time.time()) - 3600),  # expired
        id_token("n-1", email_verified=False),
    ],
)
def test_bad_tokens_are_rejected(token: str) -> None:
    with pytest.raises(AuthError):
        exchange(FakeIdp(token))


def test_microsoft_tenant_issuer_template() -> None:
    template = "https://login.microsoftonline.com/{tenantid}/v2.0"
    good = id_token("n-1", iss="https://login.microsoftonline.com/t-9/v2.0", tid="t-9")
    wrong = id_token("n-1", iss="https://login.microsoftonline.com/t-9/v2.0", tid="t-8")

    assert exchange(FakeIdp(good, issuer=template))
    with pytest.raises(AuthError):
        exchange(FakeIdp(wrong, issuer=template))


class Clock:
    def __init__(self) -> None:
        self.now_value = datetime(2026, 11, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self.now_value


def test_full_flow_state_is_single_use_and_expires() -> None:
    store, clock = InMemoryStore(), Clock()
    idp = FakeIdp("")
    service = AuthService(
        lambda: FakeUnitOfWork(store),
        {"google": provider(idp)},
        clock,
        frozenset({"person@example.com"}),
    )
    url = asyncio.run(service.start("google", "https://app/cb", None))
    query = parse_qs(urlparse(url).query)
    state = query["state"][0]
    request = store.login_requests[state]
    assert query["code_challenge"] == [code_challenge(request.code_verifier)]
    idp.token = id_token(request.nonce)

    signed_in = asyncio.run(service.finish("google", state, "c", "https://app/cb"))
    assert signed_in.user.is_admin and signed_in.token
    with pytest.raises(AuthError, match="not valid any more"):
        asyncio.run(service.finish("google", state, "c", "https://app/cb"))

    late = parse_qs(urlparse(asyncio.run(service.start("google", "x", None))).query)["state"][0]
    clock.now_value += timedelta(minutes=11)
    with pytest.raises(AuthError, match="took too long"):
        asyncio.run(service.finish("google", late, "c", "x"))


def test_dev_login_is_never_on_in_prod() -> None:
    assert Settings(env=Environment.DEV, dev_login=True).is_dev_login_enabled
    assert not Settings(env=Environment.PROD, dev_login=True).is_dev_login_enabled
    assert not Settings(env=Environment.DEV, dev_login=False).is_dev_login_enabled
