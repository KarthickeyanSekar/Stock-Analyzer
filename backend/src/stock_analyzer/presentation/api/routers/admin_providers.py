"""Admin > Data Providers: list, credentials (write-only), test and primary provider."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.providers import (
    CredentialsBody,
    ProviderResponse,
    ProviderTestResponse,
)

router = APIRouter(prefix="/api/admin/providers", tags=["admin"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=list[ProviderResponse], summary="List providers")
async def list_providers(container: ContainerDep) -> list[ProviderResponse]:
    """Return every provider plugin with masked credentials and which one is primary."""
    return [
        ProviderResponse(
            plugin_name=p.plugin_name,
            kind=p.kind,
            display_name=p.display_name,
            is_enabled=p.is_enabled,
            is_synthetic=p.is_synthetic,
            is_primary=p.is_primary,
            credential_fields=list(p.credential_fields),
            credential_hints=p.credential_hints,
            has_credentials=p.has_credentials,
        )
        for p in await container.provider_admin.list_all()
    ]


@router.put(
    "/{plugin_name}/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Save credentials",
)
async def save_credentials(
    plugin_name: str, body: CredentialsBody, container: ContainerDep
) -> Response:
    """Encrypt and store credentials. They are never returned, only their last 4 characters."""
    await container.provider_admin.save_credentials(plugin_name, body.values)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{plugin_name}/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove credentials",
)
async def delete_credentials(plugin_name: str, container: ContainerDep) -> Response:
    """Remove the stored credentials (not while the provider is primary)."""
    await container.provider_admin.delete_credentials(plugin_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plugin_name}/test", response_model=ProviderTestResponse, summary="Test a connection"
)
async def test_provider(plugin_name: str, container: ContainerDep) -> ProviderTestResponse:
    """Check that the provider can reach its data source with the stored credentials."""
    check = await container.provider_admin.test_connection(plugin_name)
    return ProviderTestResponse(plugin_name=plugin_name, is_ok=check.is_ok, message=check.message)


@router.put("/{plugin_name}/primary", status_code=status.HTTP_204_NO_CONTENT, summary="Set primary")
async def set_primary(plugin_name: str, container: ContainerDep) -> Response:
    """Use this provider for prices and fundamentals (its credentials must be set)."""
    await container.provider_admin.set_primary(plugin_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
