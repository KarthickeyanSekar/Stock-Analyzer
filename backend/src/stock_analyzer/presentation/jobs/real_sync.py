"""Job: load real prices for the stocks picked in Admin > Data sources (``make real-sync``)."""

import asyncio
import logging
from datetime import date, timedelta

from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)
HISTORY_YEARS = 10


async def run() -> None:
    """Backfill the last ten years for each picked stock; other stocks keep synthetic data."""
    container = build_container()
    end = date.today()
    results = await container.real_data_sync.sync(end - timedelta(days=365 * HISTORY_YEARS), end)
    if not results:
        logger.info("no stocks picked: pick up to five in Admin > Data sources")
    for result in results:
        if result.error:
            logger.warning("%s: failed: %s", result.symbol, result.error)
        else:
            logger.info("%s: loaded %d candles", result.symbol, result.candles)


if __name__ == "__main__":
    asyncio.run(run())
