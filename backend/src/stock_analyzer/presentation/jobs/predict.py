"""Job: predict every stock and category (``make predict``): ACTIVE ML model, else baseline."""

import asyncio
import logging

from stock_analyzer.application.use_cases.ml.run_predictions import RunPredictions
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)


async def run() -> None:
    """Store one prediction per stock x holding category as of each stock's last close."""
    container = build_container()
    result = await RunPredictions(
        container.uow_factory, container.trainer, container.settings.models_dir
    ).execute()
    logger.info("stored %d ML and %d baseline predictions", result.ml, result.baseline)


if __name__ == "__main__":
    asyncio.run(run())
