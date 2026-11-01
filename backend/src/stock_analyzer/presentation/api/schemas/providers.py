"""Admin > Data Providers response models."""

from pydantic import BaseModel, ConfigDict


class ProviderResponse(BaseModel):
    """A configured provider."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plugin_name": "mock",
                    "kind": "MARKET_DATA",
                    "display_name": "Mock (synthetic data)",
                    "is_enabled": True,
                }
            ]
        }
    )

    plugin_name: str
    kind: str
    display_name: str
    is_enabled: bool


class ProviderTestResponse(BaseModel):
    """Result of a connection test."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"plugin_name": "mock", "is_ok": True}]}
    )

    plugin_name: str
    is_ok: bool
