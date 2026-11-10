"""Cache layer for landscape data with TTL support."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CachedItem:
    """Cached data for a single landscape item."""

    key: str
    stars: int | None
    description: str | None
    favicon_url: str | None
    favicon_path: str | None
    fetched_at: float
    source: str = "github"  # github | url


def _load_cache(cache_file: Path) -> dict[str, CachedItem]:
    """Load cache data from disk, returning empty dict if missing."""
    if not cache_file.exists():
        return {}
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    return {
        key: CachedItem(**value) for key, value in data.items()
    }


def _save_cache(cache_file: Path, data: dict[str, CachedItem]) -> None:
    """Persist cache data to disk."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    serializable: dict[str, Any] = {
        key: asdict(item) for key, item in data.items()
    }
    cache_file.write_text(
        json.dumps(serializable, indent=2), encoding="utf-8"
    )


class Cache:
    """Local JSON cache with TTL (time-to-live) support."""

    cache_file: Path
    ttl_seconds: float  # seconds
    _data: dict[str, CachedItem]

    def __init__(self, cache_file: Path, ttl_seconds: float = 86400.0) -> None:
        self.cache_file = cache_file
        self.ttl_seconds = ttl_seconds
        self._data = _load_cache(cache_file)
        # Ensure file exists
        if not cache_file.exists():
            _save_cache(cache_file, self._data)

    def _persist(self) -> None:
        """Sync in-memory data to disk."""
        _save_cache(self.cache_file, self._data)

    def get(self, key: str) -> CachedItem | None:
        """Get cached item if not expired."""
        item = self._data.get(key)
        if item is None:
            return None
        if time.time() - item.fetched_at < self.ttl_seconds:
            return item
        return None

    def put(self, item: CachedItem) -> None:
        """Store or update a cached item."""
        self._data[item.key] = item
        self._persist()

    def refresh(self, key: str) -> None:
        """Remove cached item to force refresh."""
        self._data = {k: v for k, v in self._data.items() if k != key}
        self._persist()

    def clear(self) -> None:
        """Clear all cached data."""
        self._data = {}
        self._persist()

    def keys(self) -> list[str]:
        """Return all cached keys."""
        return [item.key for item in self._data.values()]

    def remove_expired(self) -> int:
        """Remove expired entries. Return count of removed items."""
        now = time.time()
        before = len(self._data)
        self._data = {
            k: v
            for k, v in self._data.items()
            if now - v.fetched_at < self.ttl_seconds
        }
        if before != len(self._data):
            self._persist()
        return before - len(self._data)

    def recent_entries(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most recently fetched cache entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of dicts with ``key``, ``stars``, and ``fetched_at``
            (formatted as ``YYYY-MM-DD HH:MM``), sorted newest first.
        """
        sorted_items = sorted(
            self._data.values(),
            key=lambda item: item.fetched_at,
            reverse=True,
        )
        return [
            {
                "key": item.key,
                "stars": item.stars,
                "fetched_at": datetime.fromtimestamp(item.fetched_at).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
            for item in sorted_items[:limit]
        ]
