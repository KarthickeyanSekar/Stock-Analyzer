"""Job: compute baseline predictions for every stock and category (``make predict``)."""

import asyncio
import logging

from stock_analyzer.application.use_cases.prediction.run_baseline_predictions import (
    RunBaselinePredictions,
)
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)


async def run() -> None:
    """Store one prediction per stock x holding category as of each stock's last close."""
    container = build_container()
    stored = await RunBaselinePredictions(container.uow_factory).execute()
    logger.info("stored %d predictions", stored)


if __name__ == "__main__":
    asyncio.run(run())
