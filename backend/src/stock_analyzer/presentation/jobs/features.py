"""Job: build point-in-time features and training labels (``make features``)."""

import asyncio
import logging

from stock_analyzer.application.use_cases.ml.build_features import BuildFeaturesAndLabels
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)


async def run() -> None:
    """Build every sample date's features and every category's labels; safe to re-run."""
    container = build_container()
    result = await BuildFeaturesAndLabels(container.uow_factory).execute()
    logger.info(
        "built features for %d dates (%d vectors) and %d labels",
        result.dates,
        result.features,
        result.labels,
    )


if __name__ == "__main__":
    asyncio.run(run())
