"""Settings: journal defaults (paper capital, risk %, tolerance, stop %)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import get_container
from stock_analyzer.presentation.api.schemas.trade_plans import (
    JournalSettingsBody,
    JournalSettingsResponse,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("/journal", response_model=JournalSettingsResponse, summary="Journal settings")
async def get_journal_settings(container: ContainerDep) -> JournalSettingsResponse:
    """Return the journal defaults (built-in defaults until saved)."""
    return JournalSettingsResponse.from_domain(await container.journal_settings.get())


@router.put("/journal", response_model=JournalSettingsResponse, summary="Save journal settings")
async def save_journal_settings(
    body: JournalSettingsBody, container: ContainerDep
) -> JournalSettingsResponse:
    """Replace the journal defaults; plans already started keep their own values."""
    return JournalSettingsResponse.from_domain(
        await container.journal_settings.update(body.to_domain())
    )
