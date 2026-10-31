"""Trade journal: start, list, read and close plans."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from stock_analyzer.application.use_cases.journal.trade_plans import (
    CloseTradePlanRequest,
    CreateTradePlanRequest,
)
from stock_analyzer.bootstrap import Container
from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.trade_plans import (
    CloseTradePlanBody,
    CreateTradePlanBody,
    TradePlanResponse,
)

router = APIRouter(prefix="/api/trade-plans", tags=["trade journal"])
ContainerDep = Annotated[Container, Depends(get_container)]


async def _respond(container: Container, plans: list[TradePlan]) -> list[TradePlanResponse]:
    symbols = await container.stock_queries.symbols({plan.stock_id for plan in plans})
    return [TradePlanResponse.from_domain(p, symbols.get(p.stock_id, "?")) for p in plans]


@router.post(
    "",
    response_model=TradePlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a plan",
)
async def create_trade_plan(
    body: CreateTradePlanBody, container: ContainerDep
) -> TradePlanResponse:
    """Start a plan; the latest prediction for the category is locked into it."""
    plan = await container.trade_plans.create(CreateTradePlanRequest(**body.model_dump()))
    return (await _respond(container, [plan]))[0]


@router.get("", response_model=list[TradePlanResponse], summary="List plans")
async def list_trade_plans(container: ContainerDep) -> list[TradePlanResponse]:
    """Return every plan, newest first."""
    return await _respond(container, await container.trade_plans.list_all())


@router.get("/{plan_id}", response_model=TradePlanResponse, summary="Get one plan")
async def get_trade_plan(plan_id: int, container: ContainerDep) -> TradePlanResponse:
    """Return one plan."""
    return (await _respond(container, [await container.trade_plans.get(plan_id)]))[0]


@router.post("/{plan_id}/close", response_model=TradePlanResponse, summary="Close a plan")
async def close_trade_plan(
    plan_id: int, body: CloseTradePlanBody, container: ContainerDep
) -> TradePlanResponse:
    """Record the exit. The outcome (SUCCESS / PARTIAL / FAILURE) is calculated, never sent."""
    plan = await container.trade_plans.close(
        CloseTradePlanRequest(plan_id=plan_id, **body.model_dump())
    )
    return (await _respond(container, [plan]))[0]
