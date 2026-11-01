"""Map domain and application errors to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from stock_analyzer.application.errors import (
    AuthError,
    ConfigurationError,
    ForbiddenError,
    NotFoundError,
    ProviderError,
)
from stock_analyzer.domain.journal.trade_plan import PlanAlreadyClosedError
from stock_analyzer.domain.shared.errors import DomainError


def register_error_handlers(app: FastAPI) -> None:
    """Install handlers: 401/403 auth, 404, 409, 502 provider, 503 config, 422 others."""

    @app.exception_handler(NotFoundError)
    async def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PlanAlreadyClosedError)
    async def conflict(_: Request, exc: PlanAlreadyClosedError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(AuthError)
    async def unauthorised(_: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden(_: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ProviderError)
    async def provider_failed(_: Request, exc: ProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ConfigurationError)
    async def not_configured(_: Request, exc: ConfigurationError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def business_rule(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
