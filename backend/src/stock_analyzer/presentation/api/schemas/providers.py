"""Admin > Data Providers request and response models (secrets are write-only)."""

from pydantic import BaseModel, ConfigDict, Field


class ProviderResponse(BaseModel):
    """A provider plugin with masked credentials."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plugin_name": "eodhd",
                    "kind": "MARKET_DATA",
                    "display_name": "EODHD",
                    "is_enabled": True,
                    "is_synthetic": False,
                    "is_primary": False,
                    "credential_fields": ["api_token"],
                    "credential_hints": {"api_token": "1a2b"},
                    "has_credentials": True,
                }
            ]
        }
    )

    plugin_name: str
    kind: str
    display_name: str
    is_enabled: bool
    is_synthetic: bool
    is_primary: bool
    credential_fields: list[str]
    credential_hints: dict[str, str] = Field(description="Last 4 characters only")
    has_credentials: bool


class ProviderTestResponse(BaseModel):
    """Result of a connection test (the message never contains secrets)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plugin_name": "eodhd",
                    "is_ok": True,
                    "message": "Connected (monthly): 120 of 100000 API calls used today",
                }
            ]
        }
    )

    plugin_name: str
    is_ok: bool
    message: str


class CredentialsBody(BaseModel):
    """Credential fields to store encrypted, e.g. ``{"api_token": "..."}``."""

    values: dict[str, str] = Field(examples=[{"api_token": "your-eodhd-token"}])
