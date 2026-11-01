"""Stock search, prices and predictions."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.stocks import (
    CandleResponse,
    FundamentalsResponse,
    PredictionResponse,
    StockOverviewResponse,
    StockPredictionsResponse,
    StockResponse,
)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("", response_model=list[StockResponse], summary="Search stocks")
async def search_stocks(
    container: ContainerDep,
    query: Annotated[str | None, Query(description="Part of the symbol or name")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[StockResponse]:
    """Return stocks whose symbol or name contains ``query``."""
    stocks = await container.stock_queries.search(query, limit)
    return [StockResponse.from_domain(stock) for stock in stocks]


@router.get(
    "/overview", response_model=list[StockOverviewResponse], summary="Stocks table overview"
)
async def stocks_overview(container: ContainerDep) -> list[StockOverviewResponse]:
    """Return every stock with last close, day change, 1Y return and the 1Y prediction."""
    rows = await container.stock_queries.overview()
    return [StockOverviewResponse.from_domain(row) for row in rows]


@router.get("/{symbol}", response_model=StockResponse, summary="Get one stock")
async def get_stock(symbol: str, container: ContainerDep) -> StockResponse:
    """Return one stock by NSE symbol."""
    return StockResponse.from_domain(await container.stock_queries.get(symbol))


@router.get("/{symbol}/prices", response_model=list[CandleResponse], summary="Daily candles")
async def get_prices(
    symbol: str,
    container: ContainerDep,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> list[CandleResponse]:
    """Return daily candles between ``from`` and ``to`` (inclusive)."""
    candles = await container.stock_queries.prices(symbol, start, end)
    return [CandleResponse.from_domain(candle) for candle in candles]


@router.get(
    "/{symbol}/fundamentals",
    response_model=list[FundamentalsResponse],
    summary="Quarterly fundamentals",
)
async def get_fundamentals(symbol: str, container: ContainerDep) -> list[FundamentalsResponse]:
    """Return the stock's quarterly results, oldest first."""
    quarters = await container.stock_queries.fundamentals(symbol)
    return [FundamentalsResponse.from_domain(quarter) for quarter in quarters]


@router.get(
    "/{symbol}/predictions",
    response_model=StockPredictionsResponse,
    summary="Latest prediction per holding category",
)
async def get_predictions(symbol: str, container: ContainerDep) -> StockPredictionsResponse:
    """Return the latest baseline prediction for every holding category."""
    result = await container.stock_queries.predictions(symbol)
    return StockPredictionsResponse(
        stock=StockResponse.from_domain(result.stock),
        last_close=CandleResponse.from_domain(result.last_close) if result.last_close else None,
        predictions=[PredictionResponse.from_domain(p) for p in result.predictions],
    )
