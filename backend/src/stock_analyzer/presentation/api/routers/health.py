"""Health check endpoint used by Docker and the frontend."""

from importlib.metadata import version
from typing import Annotated

from fastapi import APIRouter, Depends

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.health import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def get_health(container: Annotated[Container, Depends(get_container)]) -> HealthResponse:
    """Report that the API is up, with its environment and version."""
    return HealthResponse(
        status="ok",
        env=container.settings.env.value,
        version=version("stock-analyzer"),
        server_time=container.clock.now(),
    )
