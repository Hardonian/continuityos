"""Unit tests for Sovereign Event Streaming module.

Targets: streaming.py coverage from 76% → 100%.
"""

from __future__ import annotations

from unittest.mock import patch

from continuityos.streaming import (
    GLOBAL_EVENT_BUS,
    SovereignEvent,
    SovereignEventBus,
    sse_event_streamer,
)


def _make_event(
    event_type: str = "TEST_EVENT",
    domain: str = "MARITIME",
    corridor_id: str = "CORR-ARCTIC",
    severity: str = "INFO",
) -> SovereignEvent:
    return SovereignEvent(
        domain=domain,
        event_type=event_type,
        corridor_id=corridor_id,
        severity=severity,
        title=f"Test {event_type}",
    )


class TestSovereignEventBus:
    """Test the async pub-sub event bus."""

    def test_empty_bus_recent_events(self) -> None:
        bus = SovereignEventBus(buffer_size=10)
        assert bus.get_recent_events() == []

    async def test_publish_and_recent_events(self) -> None:
        bus = SovereignEventBus(buffer_size=10)
        event = _make_event()

        await bus.publish(event)

        recent = bus.get_recent_events()
        assert len(recent) == 1
        assert recent[0].event_type == "TEST_EVENT"

    async def test_circular_buffer_overflow(self) -> None:
        bus = SovereignEventBus(buffer_size=3)

        for i in range(5):
            await bus.publish(_make_event(event_type=f"EVT_{i}"))

        recent = bus.get_recent_events()
        assert len(recent) == 3
        # Only the last 3 should be present
        assert [e.event_type for e in recent] == ["EVT_2", "EVT_3", "EVT_4"]

    async def test_recent_events_limit(self) -> None:
        bus = SovereignEventBus(buffer_size=100)

        for i in range(10):
            await bus.publish(_make_event(event_type=f"EVT_{i}"))

        limited = bus.get_recent_events(limit=3)
        assert len(limited) == 3

    async def test_subscribe_and_receive(self) -> None:
        bus = SovereignEventBus(buffer_size=10)

        queue = await bus.subscribe()
        await bus.publish(_make_event(event_type="SUBSCRIBED"))
        received = queue.get_nowait()
        assert received.event_type == "SUBSCRIBED"

    async def test_unsubscribe(self) -> None:
        bus = SovereignEventBus(buffer_size=10)

        queue = await bus.subscribe()
        assert len(bus._subscribers) == 1
        await bus.unsubscribe(queue)
        assert len(bus._subscribers) == 0
        # Unsubscribing again is a no-op
        await bus.unsubscribe(queue)
        assert len(bus._subscribers) == 0

    async def test_dead_subscriber_eviction(self) -> None:
        """When a subscriber queue is full, it gets evicted on next publish."""
        bus = SovereignEventBus(buffer_size=100)

        # Subscribe and simulate filled queue with maxsize=1
        import asyncio

        small_queue: asyncio.Queue[SovereignEvent] = asyncio.Queue(maxsize=1)
        async with bus._lock:
            bus._subscribers.append(small_queue)

        # Fill the queue
        await bus.publish(_make_event(event_type="FILL"))
        assert len(bus._subscribers) == 1

        # Next publish should evict the dead subscriber because put_nowait raises QueueFull
        await bus.publish(_make_event(event_type="EVICT"))
        assert len(bus._subscribers) == 0

    async def test_multiple_subscribers(self) -> None:
        bus = SovereignEventBus(buffer_size=10)

        q1 = await bus.subscribe()
        q2 = await bus.subscribe()
        await bus.publish(_make_event(event_type="MULTI"))
        e1 = q1.get_nowait()
        e2 = q2.get_nowait()
        assert e1.event_type == "MULTI"
        assert e2.event_type == "MULTI"


class TestSSEEventStreamer:
    """Test the SSE formatter generator."""

    async def test_initial_keepalive(self) -> None:
        """First yielded value should be the connection comment."""
        bus = SovereignEventBus(buffer_size=10)

        gen = sse_event_streamer(event_bus=bus)
        first = await gen.__anext__()
        await gen.aclose()
        assert ": sovereign-event-stream-connected" in first

    async def test_event_formatting(self) -> None:
        """Published events should be formatted as SSE data lines."""
        bus = SovereignEventBus(buffer_size=10)

        gen = sse_event_streamer(event_bus=bus)
        # Consume initial keepalive
        await gen.__anext__()
        # Publish an event
        await bus.publish(_make_event(event_type="DARK_FLEET_DETECTED"))
        # Get the formatted SSE
        sse = await gen.__anext__()
        await gen.aclose()

        assert "event: DARK_FLEET_DETECTED" in sse
        assert "data: " in sse
        assert sse.endswith("\n\n")

    async def test_heartbeat_on_timeout(self) -> None:
        """When wait_for times out, a keepalive heartbeat is sent."""
        bus = SovereignEventBus(buffer_size=10)

        gen = sse_event_streamer(event_bus=bus)
        # Consume initial keepalive
        await gen.__anext__()

        # Mock asyncio.wait_for to raise TimeoutError on the next call
        with patch("asyncio.wait_for", side_effect=TimeoutError):
            heartbeat = await gen.__anext__()
            assert heartbeat == ": keepalive-heartbeat\n\n"

        await gen.aclose()

    async def test_default_global_event_bus(self) -> None:
        """When event_bus is None, uses GLOBAL_EVENT_BUS."""
        gen = sse_event_streamer()
        first = await gen.__anext__()
        assert ": sovereign-event-stream-connected" in first
        await gen.aclose()
        assert GLOBAL_EVENT_BUS is not None


class TestSovereignEvent:
    """Test the event model defaults."""

    def test_defaults(self) -> None:
        event = _make_event()
        assert event.severity == "INFO"
        assert event.threat_score == 0.5
        assert event.payload == {}
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_custom_fields(self) -> None:
        event = SovereignEvent(
            domain="CYBER_SCADA",
            event_type="PORT_SCADA_FLOOD",
            corridor_id="CORR-HALIFAX",
            severity="CRITICAL",
            threat_score=0.95,
            title="SCADA flood detected",
            payload={"port": "HALIFAX", "packets_per_sec": 50000},
        )
        assert event.severity == "CRITICAL"
        assert event.threat_score == 0.95
        assert event.payload["packets_per_sec"] == 50000
