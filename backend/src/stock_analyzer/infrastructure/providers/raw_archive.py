"""Raw provider responses saved to disk, so data can be re-parsed or re-used without new API calls.

Each successful response is written as gzip JSON under
``<root>/<provider>/<YYYY-MM-DD>/<path>__<params>__<HHMMSS>.json.gz``. Credentials are never
part of the file name or content (the caller passes params without the key).
"""

import gzip
import json
import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


class RawResponseArchive:
    """Append-only archive of raw JSON responses."""

    def __init__(self, root: str | Path) -> None:
        """Write under ``root`` (created on first save)."""
        self._root = Path(root)

    def save(
        self,
        provider: str,
        path: str,
        params: Mapping[str, str],
        body: Any,  # noqa: ANN401 - raw JSON
        now: datetime | None = None,
    ) -> Path | None:
        """Store one response; a failed write is logged and never breaks the data load."""
        moment = now or datetime.now(tz=UTC)
        query = "_".join(f"{k}-{v}" for k, v in sorted(params.items()))
        name = _UNSAFE.sub("_", f"{path.strip('/')}__{query}")[:180]
        target = (
            self._root
            / provider
            / moment.strftime("%Y-%m-%d")
            / f"{name}__{moment.strftime('%H%M%S%f')}.json.gz"
        )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(target, "wt", encoding="utf-8") as file:
                json.dump(
                    {
                        "provider": provider,
                        "path": path,
                        "params": dict(params),
                        "fetched_at": moment.isoformat(),
                        "body": body,
                    },
                    file,
                )
        except OSError as error:
            logger.warning("raw response not archived (%s)", type(error).__name__)
            return None
        return target
