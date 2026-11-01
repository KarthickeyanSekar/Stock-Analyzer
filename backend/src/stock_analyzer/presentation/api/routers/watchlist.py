"""The signed-in user's watchlist."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import CurrentUser, get_container
from stock_analyzer.presentation.api.schemas.stocks import StockResponse

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=list[StockResponse], summary="My watchlist")
async def my_watchlist(user: CurrentUser, container: ContainerDep) -> list[StockResponse]:
    """Watched stocks in the order they were added."""
    return [StockResponse.from_domain(s) for s in await container.watchlist.list(user)]


@router.put("/{symbol}", status_code=status.HTTP_204_NO_CONTENT, summary="Watch a stock")
async def watch(symbol: str, user: CurrentUser, container: ContainerDep) -> Response:
    """Add the stock to the watchlist (no-op if already there)."""
    await container.watchlist.set(user, symbol, watched=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT, summary="Unwatch a stock")
async def unwatch(symbol: str, user: CurrentUser, container: ContainerDep) -> Response:
    """Remove the stock from the watchlist."""
    await container.watchlist.set(user, symbol, watched=False)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
