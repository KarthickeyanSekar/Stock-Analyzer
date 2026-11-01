"""Holding-period screener: "N days, X% -> which stocks?"."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from stock_analyzer.bootstrap import Container
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.screening import ScreenCriteria
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.screener import ScreenRowResponse

router = APIRouter(prefix="/api/screener", tags=["screener"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=list[ScreenRowResponse], summary="Screen stocks")
async def screen_stocks(  # noqa: PLR0913 - one query parameter per filter
    *,
    container: ContainerDep,
    category: HoldingCategory,
    target_pct: Annotated[int, Query(ge=1, le=50, description="Wanted return, %")],
    target_max_pct: Annotated[int | None, Query(ge=1, le=50)] = None,
    min_probability: Annotated[Decimal, Query(ge=0, le=1)] = Decimal(0),
    min_worst_pct: Annotated[
        Decimal | None, Query(le=0, description="Worst likely return (p10) at least this")
    ] = None,
    min_quality: Annotated[int, Query(ge=0, le=10)] = 0,
    sector: Annotated[list[str] | None, Query()] = None,
) -> list[ScreenRowResponse]:
    """Stocks whose latest prediction meets the filters, ranked by the target probability."""
    criteria = ScreenCriteria(
        category=category,
        target_pct=target_pct,
        target_max_pct=target_max_pct,
        min_probability=min_probability,
        min_worst_pct=min_worst_pct,
        min_quality=min_quality,
        sectors=frozenset(sector or ()),
    )
    return [ScreenRowResponse.from_domain(r) for r in await container.screener.screen(criteria)]
