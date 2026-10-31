"""FastAPI app factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from stock_analyzer.bootstrap import Container, build_container
from stock_analyzer.presentation.api.routers import health


def create_app(container: Container | None = None) -> FastAPI:
    """Build the FastAPI application with all routers registered."""
    container = container or build_container()
    app = FastAPI(title="Stock Analyzer API", version="0.1.0", openapi_url="/api/openapi.json")
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=container.settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    if container.settings.otel_enabled:
        FastAPIInstrumentor.instrument_app(app)
    return app


app = create_app()
