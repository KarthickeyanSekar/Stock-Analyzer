"""Journal settings use cases (D2.4, Q63)."""

from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.journal.settings import JournalSettings


class JournalSettingsService:
    """Read and replace the app-wide journal settings."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work per call."""
        self._uow_factory = uow_factory

    async def get(self) -> JournalSettings:
        """Return the saved settings, or the defaults."""
        async with self._uow_factory() as uow:
            return await uow.settings.get()

    async def update(self, settings: JournalSettings) -> JournalSettings:
        """Save new settings; plans already started keep the values they were started with."""
        async with self._uow_factory() as uow:
            await uow.settings.save(settings)
            await uow.commit()
        return settings
