"""Admin > Data sources: which stocks have real data, and which ones the sync job loads."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from stock_analyzer.application.use_cases.data.real_data_sync import MAX_REAL_SYNC_STOCKS
from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import CurrentAdmin, get_container
from stock_analyzer.presentation.api.schemas.data_sources import (
    DataSourceResponse,
    DataSourcesResponse,
    SetRealSyncBody,
)

router = APIRouter(prefix="/api/admin/data-sources", tags=["admin"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=DataSourcesResponse, summary="Data source per stock")
async def list_data_sources(_: CurrentAdmin, container: ContainerDep) -> DataSourcesResponse:
    """Every stock: real or synthetic prices, last candle, and whether it syncs real data."""
    sources = await container.real_data_sync.sources()
    return DataSourcesResponse(
        max_real_sync=MAX_REAL_SYNC_STOCKS,
        stocks=[DataSourceResponse.from_domain(s) for s in sources],
    )


@router.put(
    "/{symbol}/real-sync",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Pick / unpick for the real-data sync",
)
async def set_real_sync(
    symbol: str, body: SetRealSyncBody, admin: CurrentAdmin, container: ContainerDep
) -> Response:
    """At most five stocks can be picked; ``make real-sync`` then loads their real prices."""
    await container.real_data_sync.set_enabled(admin, symbol, is_enabled=body.is_enabled)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
