"""FastAPI dependencies: the wired container and the signed-in user."""

from typing import Annotated, cast

from fastapi import Depends, Request

from stock_analyzer.application.errors import AuthError, ForbiddenError
from stock_analyzer.bootstrap import Container
from stock_analyzer.domain.users.user import User

SESSION_COOKIE = "sa_session"


def get_container(request: Request) -> Container:
    """Return the container stored on the app at startup."""
    return cast(Container, request.app.state.container)


async def current_user(
    request: Request, container: Annotated[Container, Depends(get_container)]
) -> User:
    """The signed-in user (401 without a valid session)."""
    user = await container.auth.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise AuthError("please sign in")
    return user


async def current_admin(user: Annotated[User, Depends(current_user)]) -> User:
    """The signed-in admin (403 for other users)."""
    if not user.is_admin:
        raise ForbiddenError("admins only")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
CurrentAdmin = Annotated[User, Depends(current_admin)]
