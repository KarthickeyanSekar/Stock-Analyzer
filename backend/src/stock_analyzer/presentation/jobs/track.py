"""Job: store daily progress snapshots of every active plan (``make track``)."""

import asyncio
import logging

from stock_analyzer.application.use_cases.journal.track_active_plans import TrackActivePlans
from stock_analyzer.bootstrap import build_container

logger = logging.getLogger(__name__)


async def run() -> None:
    """Snapshot each active plan for every trading day it has prices; safe to re-run."""
    container = build_container()
    stored = await TrackActivePlans(container.uow_factory, container.calendar).execute()
    logger.info("stored %d plan snapshots", stored)


if __name__ == "__main__":
    asyncio.run(run())
