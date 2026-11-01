import asyncio
import copy
from datetime import date
from decimal import Decimal

import pytest
from cryptography.fernet import Fernet

from stock_analyzer.application.errors import ConfigurationError
from stock_analyzer.application.use_cases.data.switch_to_real_data import SwitchToRealData
from stock_analyzer.application.use_cases.providers.providers import ProviderAdmin
from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.infrastructure.providers.catalog import StaticPluginCatalog
from stock_analyzer.infrastructure.security.fernet_cipher import FernetCipher
from tests.eodhd_fixtures import VALID_TOKEN, client
from tests.fakes import FakeUnitOfWork, InMemoryStore


def admin(store: InMemoryStore) -> ProviderAdmin:
    return ProviderAdmin(
        lambda: FakeUnitOfWork(store),
        StaticPluginCatalog(eodhd_client=client()),
        FernetCipher(Fernet.generate_key().decode()),
    )


def test_refuses_while_mock_is_primary(seeded_store: InMemoryStore) -> None:
    store = copy.deepcopy(seeded_store)
    switch = SwitchToRealData(lambda: FakeUnitOfWork(store), admin(store))

    with pytest.raises(ConfigurationError, match="make a real provider primary"):
        asyncio.run(switch.execute(date(2020, 1, 1), date(2026, 10, 30)))
    assert store.candles  # nothing deleted


def test_replaces_synthetic_data_and_keeps_the_journal(seeded_store: InMemoryStore) -> None:
    store = copy.deepcopy(seeded_store)
    providers = admin(store)
    asyncio.run(providers.save_credentials("eodhd", {"api_token": VALID_TOKEN}))
    asyncio.run(providers.set_primary("eodhd"))
    plan = TradePlan.start(
        stock_id=1,
        category=HoldingCategory.D50,
        start_date=date(2026, 10, 1),
        planned_end_date=date(2026, 11, 20),
        entry_price=store.candles[1][date(2026, 10, 1)].close,
        target_pct=Decimal(10),
    )
    plan_id = max(store.plans, default=0) + 1
    store.plans[plan_id] = plan
    plans_before = dict(store.plans)
    store.features[("fs-v1", 1, date(2026, 10, 1))] = {"x": 1.0}

    result = asyncio.run(
        SwitchToRealData(lambda: FakeUnitOfWork(store), providers).execute(
            date(2020, 1, 1), date(2026, 10, 30)
        )
    )

    assert result.provider == "eodhd"
    assert result.deleted_candles > 0 and result.deleted_derived >= 1
    reliance = next(s for s in store.stocks.values() if s.symbol == "RELIANCE")
    assert reliance.source_provider == "eodhd"  # the SYNTHETIC badge goes away
    assert reliance.id is not None and len(store.candles[reliance.id]) == 3
    assert result.quarters == 2
    assert store.plans == plans_before  # journal kept
    assert not store.features
