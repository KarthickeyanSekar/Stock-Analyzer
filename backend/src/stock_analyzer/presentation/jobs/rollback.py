"""Job: re-activate the previous model of a category (``make model-rollback c=1Y``)."""

import asyncio
import logging
import sys

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.use_cases.ml.rollback_model import RollbackModel
from stock_analyzer.bootstrap import build_container
from stock_analyzer.domain.market.holding_category import HoldingCategory

logger = logging.getLogger(__name__)


async def run(category: HoldingCategory) -> int:
    """Roll the category back; return the process exit code."""
    container = build_container()
    try:
        restored = await RollbackModel(container.uow_factory, container.clock).execute(category)
    except NotFoundError as error:
        logger.error("%s", error)
        return 1
    logger.info("%s: %s is ACTIVE again", category.value, restored.name)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run(HoldingCategory(sys.argv[1]))))
