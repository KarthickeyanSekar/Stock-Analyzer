"""SQLAlchemy provider configuration repository."""

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.infrastructure.persistence.models import (
    ProviderAssignmentModel,
    ProviderCredentialModel,
    ProviderModel,
)


class SqlAlchemyProviderRepository:
    """Configured provider plugins."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def ensure(self, plugin_name: str, kind: str, display_name: str) -> None:
        """Register the provider if it isn't configured yet."""
        statement = insert(ProviderModel).values(
            plugin_name=plugin_name, kind=kind, display_name=display_name
        )
        await self._session.execute(
            statement.on_conflict_do_nothing(index_elements=["plugin_name"])
        )

    async def list_all(self) -> list[tuple[str, str, str, bool]]:
        """Return ``(plugin_name, kind, display_name, is_enabled)`` for every provider."""
        rows = await self._session.scalars(select(ProviderModel).order_by(ProviderModel.id))
        return [(r.plugin_name, r.kind, r.display_name, r.is_enabled) for r in rows]

    async def _id(self, plugin_name: str) -> int:
        provider_id = await self._session.scalar(
            select(ProviderModel.id).where(ProviderModel.plugin_name == plugin_name)
        )
        if provider_id is None:
            raise LookupError(f"provider {plugin_name} is not registered")
        return provider_id

    async def set_credential(
        self, plugin_name: str, field: str, encrypted: bytes, last4: str
    ) -> None:
        """Store (or replace) one encrypted credential field."""
        statement = insert(ProviderCredentialModel).values(
            provider_id=await self._id(plugin_name),
            field=field,
            value_encrypted=encrypted,
            last4=last4,
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=["provider_id", "field"],
                set_={"value_encrypted": encrypted, "last4": last4},
            )
        )

    async def delete_credentials(self, plugin_name: str) -> None:
        """Remove every credential of the provider."""
        await self._session.execute(
            delete(ProviderCredentialModel).where(
                ProviderCredentialModel.provider_id == await self._id(plugin_name)
            )
        )

    async def credentials(self, plugin_name: str) -> dict[str, bytes]:
        """Return ``{field: encrypted value}``."""
        rows = await self._session.scalars(
            select(ProviderCredentialModel).where(
                ProviderCredentialModel.provider_id == await self._id(plugin_name)
            )
        )
        return {r.field: r.value_encrypted for r in rows}

    async def credential_hints(self, plugin_name: str) -> dict[str, str]:
        """Return ``{field: last 4 characters}``."""
        rows = await self._session.scalars(
            select(ProviderCredentialModel).where(
                ProviderCredentialModel.provider_id == await self._id(plugin_name)
            )
        )
        return {r.field: r.last4 for r in rows}

    async def set_primary(self, market_code: str, data_type: str, plugin_name: str) -> None:
        """Make the provider priority 1 (the only assignment for now; failover later)."""
        await self._session.execute(
            delete(ProviderAssignmentModel).where(
                ProviderAssignmentModel.market_code == market_code,
                ProviderAssignmentModel.data_type == data_type,
            )
        )
        self._session.add(
            ProviderAssignmentModel(
                market_code=market_code,
                data_type=data_type,
                priority=1,
                provider_id=await self._id(plugin_name),
            )
        )
        await self._session.flush()

    async def primary(self, market_code: str, data_type: str) -> str | None:
        """Return the priority-1 provider's plugin name, or ``None``."""
        return await self._session.scalar(
            select(ProviderModel.plugin_name)
            .join(ProviderAssignmentModel, ProviderAssignmentModel.provider_id == ProviderModel.id)
            .where(
                ProviderAssignmentModel.market_code == market_code,
                ProviderAssignmentModel.data_type == data_type,
                ProviderAssignmentModel.priority == 1,
            )
        )
