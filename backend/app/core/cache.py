"""Cache abstraction.

A tiny protocol with two interchangeable implementations:

- `RedisCache` — production, backed by Redis.
- `InMemoryCache` — process-local dict with TTL, used for tests or when Redis
  is intentionally disabled (`CACHE_BACKEND=memory`).

The service layer depends only on the `Cache` protocol, so swapping the backend
(or mocking it) requires no changes upstream.
"""

from __future__ import annotations

import time
from typing import Protocol

from app.core.config import settings


class Cache(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    def delete_prefix(self, prefix: str) -> None: ...
    def incr(self, key: str) -> int: ...


class InMemoryCache:
    """Simple TTL cache for tests / Redis-less runs."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def get(self, key: str) -> str | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expires_at)

    def delete_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            self._store.pop(key, None)

    def incr(self, key: str) -> int:
        current = int(self.get(key) or 0) + 1
        self.set(key, str(current), 0)
        return current


class RedisCache:
    """Redis-backed cache."""

    def __init__(self, client) -> None:
        self._client = client

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if ttl_seconds:
            self._client.setex(key, ttl_seconds, value)
        else:
            self._client.set(key, value)

    def delete_prefix(self, prefix: str) -> None:
        for key in self._client.scan_iter(match=f"{prefix}*"):
            self._client.delete(key)

    def incr(self, key: str) -> int:
        return int(self._client.incr(key))


def _build_cache() -> Cache:
    if settings.CACHE_BACKEND == "memory":
        return InMemoryCache()
    try:
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL)
        client.ping()
        return RedisCache(client)
    except Exception:
        # Fail open to an in-memory cache rather than taking the API down if
        # Redis is unreachable. Caching is a performance optimization, not a
        # source of truth.
        return InMemoryCache()


_cache: Cache | None = None


def get_cache() -> Cache:
    """FastAPI dependency returning the process-wide cache."""
    global _cache
    if _cache is None:
        _cache = _build_cache()
    return _cache


def reset_cache_for_tests(cache: Cache) -> None:
    """Inject a cache implementation (used by the test suite)."""
    global _cache
    _cache = cache
