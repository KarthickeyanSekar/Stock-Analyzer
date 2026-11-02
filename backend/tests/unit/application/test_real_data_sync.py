import asyncio
import copy
import gzip
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from stock_analyzer.application.errors import ConfigurationError, NotFoundError
from stock_analyzer.application.use_cases.data.real_data_sync import (
    MAX_REAL_SYNC_STOCKS,
    RealDataSync,
    RealSyncLimitError,
)
from stock_analyzer.application.use_cases.providers.providers import ProviderAdmin
from stock_analyzer.domain.users.user import Role, User
from stock_analyzer.infrastructure.providers.catalog import StaticPluginCatalog
from stock_analyzer.infrastructure.providers.raw_archive import RawResponseArchive
from stock_analyzer.infrastructure.security.fernet_cipher import FernetCipher
from tests.eodhd_fixtures import VALID_TOKEN, client
from tests.fakes import FakeUnitOfWork, InMemoryStore

ADMIN = User(uuid4(), "admin@test.local", "Admin", "dev", "admin", role=Role.ADMIN)


def service(store: InMemoryStore, archive: RawResponseArchive | None = None) -> RealDataSync:
    providers = ProviderAdmin(
        lambda: FakeUnitOfWork(store),
        StaticPluginCatalog(eodhd_client=client(), archive=archive),
        FernetCipher(Fernet.generate_key().decode()),
    )
    return RealDataSync(lambda: FakeUnitOfWork(store), providers)


def make_eodhd_primary(store: InMemoryStore, sync: RealDataSync) -> None:
    providers = sync._providers
    asyncio.run(providers.save_credentials("eodhd", {"api_token": VALID_TOKEN}))
    asyncio.run(providers.set_primary("eodhd"))


def test_lists_every_stock_as_synthetic_and_unpicked(seeded_store: InMemoryStore) -> None:
    sources = asyncio.run(service(copy.deepcopy(seeded_store)).sources())

    assert sources and all(s.latest_source == "mock" for s in sources)
    assert not any(s.is_real_sync_enabled for s in sources)
    assert all(s.candles > 0 and s.last_trade_date for s in sources)


def test_at_most_five_stocks_can_be_picked(seeded_store: InMemoryStore) -> None:
    store = copy.deepcopy(seeded_store)
    sync = service(store)
    symbols = sorted(s.symbol for s in store.stocks.values())

    for symbol in symbols[:MAX_REAL_SYNC_STOCKS]:
        asyncio.run(sync.set_enabled(ADMIN, symbol, is_enabled=True))
    asyncio.run(sync.set_enabled(ADMIN, symbols[0], is_enabled=True))  # re-picking is fine
    with pytest.raises(RealSyncLimitError, match="at most 5"):
        asyncio.run(sync.set_enabled(ADMIN, symbols[MAX_REAL_SYNC_STOCKS], is_enabled=True))

    asyncio.run(sync.set_enabled(ADMIN, symbols[0], is_enabled=False))
    asyncio.run(sync.set_enabled(ADMIN, symbols[MAX_REAL_SYNC_STOCKS], is_enabled=True))
    assert len(store.real_sync) == MAX_REAL_SYNC_STOCKS
    assert store.audit[-1].action == "real_sync_enabled"
    with pytest.raises(NotFoundError):
        asyncio.run(sync.set_enabled(ADMIN, "NOPE", is_enabled=True))


def test_sync_refuses_while_mock_is_primary(seeded_store: InMemoryStore) -> None:
    with pytest.raises(ConfigurationError, match="make a real provider primary"):
        asyncio.run(service(copy.deepcopy(seeded_store)).sync(date(2020, 1, 1), date(2026, 10, 30)))


def test_sync_loads_only_picked_stocks_and_archives_raw_responses(
    seeded_store: InMemoryStore, tmp_path: Path
) -> None:
    store = copy.deepcopy(seeded_store)
    sync = service(store, RawResponseArchive(tmp_path))
    make_eodhd_primary(store, sync)
    tcs_before = dict(store.candles[next(i for i, s in store.stocks.items() if s.symbol == "TCS")])
    asyncio.run(sync.set_enabled(ADMIN, "RELIANCE", is_enabled=True))
    asyncio.run(sync.set_enabled(ADMIN, "INFY", is_enabled=True))  # no fixture: provider has none

    results = asyncio.run(sync.sync(date(2020, 1, 1), date(2026, 10, 30)))

    by_symbol = {r.symbol: r for r in results}
    assert by_symbol["RELIANCE"].candles == 3 and by_symbol["RELIANCE"].error is None
    assert by_symbol["INFY"].error == "provider returned no candles"
    reliance_id = next(i for i, s in store.stocks.items() if s.symbol == "RELIANCE")
    assert store.stocks[reliance_id].source_provider == "eodhd"  # SYNTHETIC badge goes away
    assert len(store.candles[reliance_id]) == 3  # synthetic history replaced
    tcs_id = next(i for i, s in store.stocks.items() if s.symbol == "TCS")
    assert store.candles[tcs_id] == tcs_before  # unpicked stocks keep synthetic data

    archived = list(tmp_path.rglob("*.json.gz"))
    assert archived and all(VALID_TOKEN not in p.name for p in archived)
    contents = [json.loads(gzip.decompress(p.read_bytes())) for p in archived]
    eod = next(c for c in contents if "RELIANCE" in c["path"])
    assert eod["provider"] == "eodhd"
    assert len(eod["body"]) == 4  # raw keeps the row the parser skipped
    assert all(VALID_TOKEN not in json.dumps(c) for c in contents)
