"""Re-activate the previous model of a category (``make model-rollback c=1Y``)."""

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.model_version import ModelVersion


class RollbackModel:
    """Retire the ACTIVE model and bring back the one active before it."""

    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        """Use ``clock`` for the activation time."""
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, category: HoldingCategory) -> ModelVersion:
        """Return the re-activated version or raise :class:`NotFoundError`."""
        async with self._uow_factory() as uow:
            restored = await uow.models.rollback(category, self._clock.now())
            if restored is None:
                raise NotFoundError(f"no earlier {category.value} model to roll back to")
            await uow.commit()
        return restored
