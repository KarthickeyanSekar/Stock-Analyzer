import pytest

from stock_analyzer.infrastructure.cache.keys import (
    ALL_KEY_SPECS,
    JOB_QUEUE,
    KeyKind,
    KeySpec,
    RedisKeys,
)
from stock_analyzer.infrastructure.config.settings import Environment


def test_quote_key_is_namespaced_by_env_and_version() -> None:
    # Arrange
    keys = RedisKeys(Environment.DEV)

    # Act
    key = keys.quote(market="IN", symbol="RELIANCE")

    # Assert
    assert key == "sa:dev:v1:quote:IN:RELIANCE"


def test_environments_never_share_keys() -> None:
    # Act
    dev_key = RedisKeys(Environment.DEV).job_lock("eod")
    prod_key = RedisKeys(Environment.PROD).job_lock("eod")

    # Assert
    assert dev_key != prod_key
    assert dev_key.startswith("sa:dev:")
    assert prod_key.startswith("sa:prod:")


@pytest.mark.parametrize("spec", ALL_KEY_SPECS, ids=lambda spec: spec.name)
def test_every_non_queue_key_has_a_ttl(spec: KeySpec) -> None:
    # Assert: only work queues may live without an expiry
    assert spec.kind is KeyKind.QUEUE or spec.ttl is not None


def test_queue_keys_have_no_ttl_so_jobs_are_never_dropped() -> None:
    assert JOB_QUEUE.ttl is None


def test_key_spec_names_are_unique() -> None:
    names = [spec.name for spec in ALL_KEY_SPECS]
    assert len(names) == len(set(names))


def test_missing_placeholder_raises() -> None:
    with pytest.raises(KeyError):
        RedisKeys(Environment.DEV).build(JOB_QUEUE)
