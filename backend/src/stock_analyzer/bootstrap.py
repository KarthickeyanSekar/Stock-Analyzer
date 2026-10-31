"""Composition root: builds and wires every dependency in one place."""

from dataclasses import dataclass

from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.infrastructure.config.settings import Settings, get_settings
from stock_analyzer.infrastructure.logging.setup import configure_logging
from stock_analyzer.infrastructure.telemetry.setup import configure_telemetry
from stock_analyzer.infrastructure.time.system_clock import SystemClock


@dataclass(frozen=True)
class Container:
    """Wired application dependencies."""

    settings: Settings
    clock: Clock


def build_container(settings: Settings | None = None) -> Container:
    """Create the dependency container for the running process."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    configure_telemetry(settings)
    return Container(settings=settings, clock=SystemClock())
