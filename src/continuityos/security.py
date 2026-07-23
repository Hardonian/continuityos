from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class RateLimitExceeded(Exception):
    retry_after: int


class FixedWindowLimiter:
    """Small process-local limiter for the single-worker reference deployment."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> int | None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now) + 1)
                return retry_after
            events.append(now)
        return None


def _provided_key(request: Request) -> str:
    return request.headers.get("x-continuity-api-key", "")


def require_api_key(request: Request) -> None:
    settings: Any = request.app.state.settings
    configured = settings.api_key
    if configured is None:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API key unavailable"
            )
        return
    supplied = _provided_key(request)
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="valid X-Continuity-API-Key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def enforce_rate_limit(request: Request) -> None:
    settings: Any = request.app.state.settings
    limiter: FixedWindowLimiter = request.app.state.rate_limiter
    identity = _provided_key(request) or (request.client.host if request.client else "unknown")
    key = hashlib.sha256(identity.encode()).hexdigest()
    retry_after = limiter.check(key, settings.rate_limit_per_minute)
    if retry_after is not None:
        raise RateLimitExceeded(retry_after)
