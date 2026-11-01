"""OpenID Connect identity providers: Google and Microsoft (Q72).

Authorization Code + PKCE (S256). The ID token from the token endpoint is verified against
the provider's JWKS: signature (RS256), issuer, audience (our client id), expiry and nonce.
"""

from typing import Any
from urllib.parse import urlencode

import httpx
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet

from stock_analyzer.application.errors import AuthError
from stock_analyzer.application.ports.auth import Identity

GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
MICROSOFT_DISCOVERY = (
    "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
)
LEEWAY_SECONDS = 60
SCOPE = "openid email profile"


class OidcIdentityProvider:
    """Implements ``IdentityProvider`` for any OIDC provider found by discovery."""

    def __init__(  # noqa: PLR0913 - an OIDC client's configuration
        self,
        *,
        name: str,
        display_name: str,
        discovery_url: str,
        client_id: str,
        client_secret: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Configure the provider; nothing is fetched until the first sign-in."""
        self._name = name
        self._display_name = display_name
        self._discovery_url = discovery_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = client or httpx.AsyncClient(timeout=15.0)
        self._config: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        """Short name (``google``, ``microsoft``)."""
        return self._name

    @property
    def display_name(self) -> str:
        """Label for the sign-in button."""
        return self._display_name

    async def _get_json(self, url: str) -> dict[str, Any]:
        try:
            response = await self._client.get(url)
        except httpx.HTTPError as error:
            raise AuthError(f"{self._display_name} is unreachable") from error
        if response.status_code != httpx.codes.OK:
            raise AuthError(f"{self._display_name} sign-in is unavailable")
        data: dict[str, Any] = response.json()
        return data

    async def _discovery(self) -> dict[str, Any]:
        if self._config is None:
            self._config = await self._get_json(self._discovery_url)
        return self._config

    async def authorization_url(
        self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
    ) -> str:
        """The provider's sign-in page with PKCE, state and nonce."""
        config = await self._discovery()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._client_id,
                "redirect_uri": redirect_uri,
                "scope": SCOPE,
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        )
        return f"{config['authorization_endpoint']}?{query}"

    async def exchange(
        self, *, code: str, code_verifier: str, redirect_uri: str, nonce: str
    ) -> Identity:
        """Exchange the code with the PKCE verifier and verify the ID token."""
        config = await self._discovery()
        try:
            response = await self._client.post(
                config["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code_verifier": code_verifier,
                },
            )
        except httpx.HTTPError as error:
            raise AuthError(f"{self._display_name} is unreachable") from error
        if response.status_code != httpx.codes.OK or "id_token" not in response.json():
            raise AuthError(f"{self._display_name} did not confirm the sign-in")
        jwks = await self._get_json(config["jwks_uri"])
        keys = KeySet.import_key_set(jwks)  # type: ignore[arg-type]  # JSON matches the TypedDict
        return self._verify(response.json()["id_token"], keys, config["issuer"], nonce)

    def _verify(self, id_token: str, keys: KeySet, issuer: str, nonce: str) -> Identity:
        try:
            claims = jwt.decode(id_token, keys, algorithms=["RS256"]).claims
            jwt.JWTClaimsRegistry(
                leeway=LEEWAY_SECONDS,
                aud={"essential": True, "value": self._client_id},
                exp={"essential": True},
                sub={"essential": True},
                nonce={"essential": True, "value": nonce},
            ).validate(claims)
        except (JoseError, ValueError) as error:
            raise AuthError("the sign-in could not be verified") from error
        # Microsoft's multi-tenant issuer is a template: .../{tenantid}/v2.0
        expected_issuer = issuer.replace("{tenantid}", str(claims.get("tid", "")))
        if claims.get("iss") != expected_issuer:
            raise AuthError("the sign-in could not be verified")
        email = claims.get("email") or claims.get("preferred_username")
        if not email or claims.get("email_verified") is False:
            raise AuthError(f"{self._display_name} did not share a verified email")
        return Identity(
            provider=self._name,
            subject=str(claims["sub"]),
            email=str(email).lower(),
            name=str(claims.get("name") or email),
        )
