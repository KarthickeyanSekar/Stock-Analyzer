"""Admin > Data Providers response models."""

from pydantic import BaseModel


class ProviderResponse(BaseModel):
    """A configured provider."""

    plugin_name: str
    kind: str
    display_name: str
    is_enabled: bool


class ProviderTestResponse(BaseModel):
    """Result of a connection test."""

    plugin_name: str
    is_ok: bool
