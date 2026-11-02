"""Journal settings use cases (D2.4; per user since Phase 5b)."""

from uuid import UUID

from stock_analyzer.application.ports.auth import AuditEntry
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.journal.settings import JournalSettings

AUDITED_SETTINGS = ("paper_capital", "risk_pct", "success_tolerance_pp", "default_stop_pct")


class JournalSettingsService:
    """Read and replace the app-wide journal settings."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work per call."""
        self._uow_factory = uow_factory

    async def get(self, user_id: UUID | None = None) -> JournalSettings:
        """Return the user's saved settings, or the defaults."""
        async with self._uow_factory() as uow:
            return await uow.settings.get(user_id)

    async def update(
        self, settings: JournalSettings, user_id: UUID | None = None
    ) -> JournalSettings:
        """Save new settings; plans already started keep the values they were started with."""
        async with self._uow_factory() as uow:
            await uow.settings.save(settings, user_id)
            await uow.audit.add(
                AuditEntry(
                    None,
                    user_id,
                    "settings_changed",
                    {name: str(getattr(settings, name)) for name in AUDITED_SETTINGS},
                )
            )
            await uow.commit()
        return settings
