"""Admin > Data sources models."""

from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.config import JsonDict

from stock_analyzer.application.ports.repositories import StockDataSource
from stock_analyzer.presentation.api.schemas.stocks import SYNTHETIC_PROVIDERS

EXAMPLE: JsonDict = {
    "symbol": "RELIANCE",
    "name": "Reliance Industries Ltd",
    "latest_source": "eodhd",
    "is_real": True,
    "last_trade_date": "2026-10-30",
    "candles": 2480,
    "is_real_sync_enabled": True,
}


class DataSourceResponse(BaseModel):
    """Where one stock's prices come from, and whether it is picked for the real-data sync."""

    model_config = ConfigDict(json_schema_extra={"examples": [EXAMPLE]})

    symbol: str
    name: str
    latest_source: str | None
    is_real: bool
    last_trade_date: date | None
    candles: int
    is_real_sync_enabled: bool

    @classmethod
    def from_domain(cls, source: StockDataSource) -> "DataSourceResponse":
        """Map a data source row."""
        return cls(
            symbol=source.stock.symbol,
            name=source.stock.name,
            latest_source=source.latest_source,
            is_real=source.latest_source is not None
            and source.latest_source not in SYNTHETIC_PROVIDERS,
            last_trade_date=source.last_trade_date,
            candles=source.candles,
            is_real_sync_enabled=source.is_real_sync_enabled,
        )


class DataSourcesResponse(BaseModel):
    """Every stock's data source plus the sync limit."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"max_real_sync": 5, "stocks": [EXAMPLE]}]}
    )

    max_real_sync: int
    stocks: list[DataSourceResponse]


class SetRealSyncBody(BaseModel):
    """Pick or unpick a stock for the real-data sync."""

    is_enabled: bool
