"""Job: replace synthetic data with real data from the primary provider (``make real-data``)."""

import asyncio
import logging
from datetime import date, timedelta

from stock_analyzer.application.use_cases.data.switch_to_real_data import SwitchToRealData
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)
HISTORY_YEARS = 10


async def run() -> None:
    """Delete synthetic data and backfill the last ten years from the primary provider."""
    container = build_container()
    end = date.today()
    result = await SwitchToRealData(container.uow_factory, container.provider_admin).execute(
        end - timedelta(days=365 * HISTORY_YEARS), end
    )
    logger.info(
        "%s: removed %d synthetic candles, %d quarters, %d derived rows; "
        "loaded %d stocks, %d candles, %d quarters",
        result.provider,
        result.deleted_candles,
        result.deleted_quarters,
        result.deleted_derived,
        result.stocks,
        result.candles,
        result.quarters,
    )


if __name__ == "__main__":
    asyncio.run(run())
