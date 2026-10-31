"""Map domain and application errors to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.domain.journal.trade_plan import PlanAlreadyClosedError
from stock_analyzer.domain.shared.errors import DomainError


def register_error_handlers(app: FastAPI) -> None:
    """Install handlers: 404 not found, 409 conflict, 422 other business-rule errors."""

    @app.exception_handler(NotFoundError)
    async def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PlanAlreadyClosedError)
    async def conflict(_: Request, exc: PlanAlreadyClosedError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def business_rule(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
