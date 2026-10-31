"""Admin > Data Providers (POC: list and test; credentials and priorities come later)."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.providers import (
    ProviderResponse,
    ProviderTestResponse,
)

router = APIRouter(prefix="/api/admin/providers", tags=["admin"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=list[ProviderResponse], summary="List providers")
async def list_providers(container: ContainerDep) -> list[ProviderResponse]:
    """Return every configured provider."""
    providers = await container.provider_admin.list_all()
    return [ProviderResponse(**asdict(p)) for p in providers]


@router.post(
    "/{plugin_name}/test", response_model=ProviderTestResponse, summary="Test a connection"
)
def test_provider(plugin_name: str, container: ContainerDep) -> ProviderTestResponse:
    """Check that the provider can reach its data source."""
    return ProviderTestResponse(
        plugin_name=plugin_name, is_ok=container.provider_admin.test_connection(plugin_name)
    )
