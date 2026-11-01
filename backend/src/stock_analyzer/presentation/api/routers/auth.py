"""Sign-in (OIDC + PKCE, dev-only shortcut), sign-out and account deletion."""

from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from stock_analyzer.application.errors import AuthError
from stock_analyzer.application.use_cases.auth.auth import SESSION_LIFETIME, SignedIn
from stock_analyzer.bootstrap import Container
from stock_analyzer.infrastructure.config.settings import Environment
from stock_analyzer.presentation.api.dependencies import (
    SESSION_COOKIE,
    CurrentUser,
    get_container,
)
from stock_analyzer.presentation.api.schemas.auth import (
    DevLoginBody,
    MeResponse,
    ProviderOption,
    SignInOptionsResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
ContainerDep = Annotated[Container, Depends(get_container)]


def _set_cookie(response: Response, container: Container, signed_in: SignedIn) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        signed_in.token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        samesite="lax",  # sent on the redirect back from the identity provider
        secure=container.settings.env is Environment.PROD,
        path="/",
    )


def _redirect_uri(container: Container, provider: str) -> str:
    return f"{container.settings.public_url}/api/auth/callback/{provider}"


@router.get("/options", response_model=SignInOptionsResponse, summary="Sign-in options")
async def sign_in_options(container: ContainerDep) -> SignInOptionsResponse:
    """The configured identity providers and whether the dev sign-in is on."""
    auth = container.auth
    return SignInOptionsResponse(
        providers=[ProviderOption(name=n, display_name=d) for n, d in auth.providers()],
        dev_login=auth.is_dev_login_enabled,
    )


@router.get("/login/{provider}", summary="Start a sign-in", response_class=RedirectResponse)
async def start_sign_in(
    provider: str,
    container: ContainerDep,
    invite_code: Annotated[str | None, Query(max_length=32)] = None,
) -> RedirectResponse:
    """Redirect to the provider (PKCE, state and nonce are kept server-side)."""
    try:
        url = await container.auth.start(provider, _redirect_uri(container, provider), invite_code)
    except AuthError as error:
        return RedirectResponse(f"/sign-in?error={quote(str(error))}", status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url, status.HTTP_303_SEE_OTHER)


@router.get("/callback/{provider}", summary="Sign-in callback", response_class=RedirectResponse)
async def finish_sign_in(
    provider: str,
    container: ContainerDep,
    state: str = "",
    code: str = "",
    error: str = "",
) -> RedirectResponse:
    """Verify the sign-in, start a session and go to the app (or back with a message)."""
    try:
        if error or not state or not code:
            raise AuthError("the sign-in was cancelled")
        signed_in = await container.auth.finish(
            provider, state, code, _redirect_uri(container, provider)
        )
    except AuthError as failure:
        return RedirectResponse(f"/sign-in?error={quote(str(failure))}", status.HTTP_303_SEE_OTHER)
    response = RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    _set_cookie(response, container, signed_in)
    return response


@router.post("/dev-login", response_model=MeResponse, summary="Dev-only sign-in")
async def dev_login(body: DevLoginBody, container: ContainerDep, response: Response) -> MeResponse:
    """Sign in with just an email (``SA_DEV_LOGIN=true``, never in prod)."""
    signed_in = await container.auth.dev_login(body.email, body.invite_code)
    _set_cookie(response, container, signed_in)
    return MeResponse.from_domain(signed_in.user)


@router.get("/me", response_model=MeResponse, summary="The signed-in user")
async def me(user: CurrentUser) -> MeResponse:
    """Who is signed in (401 when nobody)."""
    return MeResponse.from_domain(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
async def logout(request: Request, container: ContainerDep) -> Response:
    """End this browser's session."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        await container.auth.sign_out(token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my account")
async def delete_me(user: CurrentUser, container: ContainerDep) -> Response:
    """Delete the account with its plans, settings, watchlist and sessions."""
    await container.auth.delete_account(user)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
