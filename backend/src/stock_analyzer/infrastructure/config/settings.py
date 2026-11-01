"""Application settings loaded from environment variables (prefix ``SA_``)."""

from enum import StrEnum
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment the app is running in."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class TelemetryExporter(StrEnum):
    """Where OpenTelemetry data is sent."""

    OTLP = "otlp"  # to a collector, e.g. the Grafana otel-lgtm container
    FILE = "file"  # JSON Lines files on disk, no extra services


class Settings(BaseSettings):
    """Bootstrap configuration; provider credentials live encrypted in the database."""

    model_config = SettingsConfigDict(env_prefix="SA_", env_file=".env", extra="ignore")

    env: Environment = Environment.DEV
    database_url: str = "postgresql+asyncpg://stock_analyzer:stock_analyzer@db:5432/stock_analyzer"
    redis_url: str = "redis://redis:6379/0"
    master_key: SecretStr = SecretStr("")
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"
    cors_origins: list[str] = ["http://localhost:5173"]
    otel_enabled: bool = False
    otel_exporter: TelemetryExporter = TelemetryExporter.OTLP
    otel_endpoint: str = "http://localhost:4318"
    otel_file_dir: str = "telemetry"
    # Trained model files and evaluation reports (relative to the backend directory).
    models_dir: str = "var/models"
    reports_dir: str = "var/reports"
    code_version: str = "unknown"
    otel_export_interval_ms: int = 15_000
    otel_service_name: str = "stock-analyzer-api"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
