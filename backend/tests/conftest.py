from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from stock_analyzer.bootstrap import Container
from stock_analyzer.infrastructure.config.settings import Environment, Settings
from stock_analyzer.main import create_app

FIXED_NOW = datetime(2026, 1, 2, 9, 15, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return FIXED_NOW


@pytest.fixture
def client() -> Iterator[TestClient]:
    container = Container(settings=Settings(env=Environment.TEST), clock=FixedClock())
    with TestClient(create_app(container)) as test_client:
        yield test_client
