"""Registry of every Redis key: its pattern, format version and expiry.

Redis has no schema or migrations, so this module is the single source of truth.
Rules (docs/17-database-backend.md):
- No key is built anywhere else in the code.
- Keys are namespaced ``sa:{env}:{version}:...`` so environments never collide.
- Every cache key has a TTL; only work queues may live without one.
- Changing a value's format means a new version (``v2``); old keys simply expire.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from stock_analyzer.infrastructure.config.settings import Environment

KEY_PREFIX = "sa"


class KeyKind(StrEnum):
    """What a key is used for; decides whether it may live without a TTL."""

    CACHE = "cache"
    QUEUE = "queue"
    LOCK = "lock"
    RATE_LIMIT = "rate_limit"


@dataclass(frozen=True, slots=True)
class KeySpec:
    """Definition of one family of Redis keys."""

    name: str
    kind: KeyKind
    version: str
    pattern: str
    ttl: timedelta | None
    purpose: str


QUOTE = KeySpec(
    name="quote",
    kind=KeyKind.CACHE,
    version="v1",
    pattern="quote:{market}:{symbol}",
    ttl=timedelta(hours=2),
    purpose="Latest hourly price snapshot for one stock",
)
JOB_QUEUE = KeySpec(
    name="jobs",
    kind=KeyKind.QUEUE,
    version="v1",
    pattern="jobs:{queue}",
    ttl=None,
    purpose="Pending background jobs, consumed by the worker",
)
JOB_LOCK = KeySpec(
    name="lock",
    kind=KeyKind.LOCK,
    version="v1",
    pattern="lock:{job}",
    ttl=timedelta(minutes=30),
    purpose="Prevents the same scheduled job from running twice",
)
PROVIDER_RATE_LIMIT = KeySpec(
    name="ratelimit",
    kind=KeyKind.RATE_LIMIT,
    version="v1",
    pattern="ratelimit:{provider}:{window}",
    ttl=timedelta(minutes=1),
    purpose="Request counter per provider and time window",
)

ALL_KEY_SPECS: tuple[KeySpec, ...] = (QUOTE, JOB_QUEUE, JOB_LOCK, PROVIDER_RATE_LIMIT)


class RedisKeys:
    """Build fully namespaced Redis keys for one environment."""

    def __init__(self, env: Environment) -> None:
        """Create a key builder for ``env`` (dev, test or prod)."""
        self._env = env

    def build(self, spec: KeySpec, **parts: str) -> str:
        """Return ``sa:{env}:{version}:{pattern}`` with every placeholder filled in."""
        return f"{self.namespace()}:{spec.version}:{spec.pattern.format(**parts)}"

    def namespace(self) -> str:
        """Return the prefix shared by all keys of this environment, e.g. ``sa:dev``."""
        return f"{KEY_PREFIX}:{self._env.value}"

    def quote(self, market: str, symbol: str) -> str:
        """Key of the latest snapshot for ``symbol`` on ``market``."""
        return self.build(QUOTE, market=market, symbol=symbol)

    def job_queue(self, queue: str) -> str:
        """Key of a background job queue."""
        return self.build(JOB_QUEUE, queue=queue)

    def job_lock(self, job: str) -> str:
        """Key of the lock that keeps ``job`` from running twice."""
        return self.build(JOB_LOCK, job=job)

    def provider_rate_limit(self, provider: str, window: str) -> str:
        """Key of the request counter for ``provider`` in ``window``."""
        return self.build(PROVIDER_RATE_LIMIT, provider=provider, window=window)
