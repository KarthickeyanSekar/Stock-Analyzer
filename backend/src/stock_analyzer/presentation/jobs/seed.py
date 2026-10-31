"""Job: load the synthetic NIFTY 50 data through the mock provider (``make seed``)."""

import asyncio
import logging

from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.bootstrap import build_container
from stock_analyzer.infrastructure.providers.mock.provider import DEFAULT_END, DEFAULT_START

logger = logging.getLogger(__name__)


async def run() -> None:
    """Backfill every instrument and candle; safe to re-run (upserts)."""
    container = build_container()
    result = await BackfillPrices(container.uow_factory, container.market_data).execute(
        DEFAULT_START, DEFAULT_END
    )
    logger.info("seeded %d stocks and %d candles", result.stocks, result.candles)


if __name__ == "__main__":
    asyncio.run(run())
