"""Health check response models."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness information returned by ``GET /api/health``."""

    status: str
    env: str
    version: str
    server_time: datetime
