"""Real-Time Sovereign Telemetry & Event Streaming Hub.

Provides:
  1. SovereignEvent: Standardized event envelope for multi-domain sensor telemetry.
  2. SovereignEventBus: Async in-memory pub-sub bus with topic subscriptions & history buffer.
  3. SSEEventStreamer: Formats live events as Server-Sent Events (SSE) for mission HUDs.
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class SovereignEvent(BaseModel):
    """Standardized event envelope across space, maritime, cyber, and environmental domains."""

    event_id: UUID = Field(default_factory=uuid4)
    domain: str  # "SPACE", "MARITIME", "ENVIRONMENTAL", "CYBER_SCADA", "CRITICAL_MINERALS"
    event_type: str  # "DARK_FLEET_DETECTED", "ORBITAL_SAR_PASS", "PERMAFROST_SETTLEMENT", etc.
    corridor_id: str
    severity: str = "INFO"  # "INFO", "WARNING", "CRITICAL", "EMERGENCY"
    threat_score: Score = 0.5
    title: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SovereignEventBus:
    """High-throughput async pub-sub event broker with circular memory buffer."""

    def __init__(self, buffer_size: int = 1000) -> None:
        self.buffer_size = buffer_size
        self._history: deque[SovereignEvent] = deque(maxlen=buffer_size)
        self._subscribers: list[asyncio.Queue[SovereignEvent]] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: SovereignEvent) -> None:
        """Publishes an event to all active subscribers and appends to circular buffer."""
        async with self._lock:
            self._history.append(event)
            dead_subscribers = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_subscribers.append(queue)
            for d in dead_subscribers:
                self._subscribers.remove(d)

    async def subscribe(self) -> asyncio.Queue[SovereignEvent]:
        """Subscribes a new listener queue to the live stream."""
        queue: asyncio.Queue[SovereignEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers.append(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[SovereignEvent]) -> None:
        """Removes a subscriber queue."""
        async with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    def get_recent_events(self, limit: int = 50) -> list[SovereignEvent]:
        """Returns recent events from the circular replay buffer."""
        items = list(self._history)
        return items[-limit:]


# Global singleton instance
GLOBAL_EVENT_BUS = SovereignEventBus()


async def sse_event_streamer(
    event_bus: SovereignEventBus | None = None,
) -> AsyncIterator[str]:
    """Asynchronous generator yielding SSE formatted strings for FastAPI StreamingResponse."""
    bus = event_bus or GLOBAL_EVENT_BUS
    queue = await bus.subscribe()

    try:
        # First send initial keep-alive comment
        yield ": sovereign-event-stream-connected\n\n"

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                event_json = event.model_dump_json()
                yield f"event: {event.event_type}\ndata: {event_json}\n\n"
            except TimeoutError:
                # Keep-alive heartbeat comment every 15s
                yield ": keepalive-heartbeat\n\n"
    finally:
        await bus.unsubscribe(queue)
