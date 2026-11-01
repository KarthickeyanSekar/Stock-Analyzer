"""Health check response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Liveness information returned by ``GET /api/health``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "env": "dev",
                    "version": "0.1.0",
                    "server_time": "2026-11-01T10:15:00Z",
                }
            ]
        }
    )

    status: str
    env: str
    version: str
    server_time: datetime
