"""Test suite for Real-Time Sovereign Telemetry & Event Streaming Hub."""

from __future__ import annotations

import asyncio

import pytest
from starlette.testclient import TestClient

from continuityos.service import create_app
from continuityos.streaming import SovereignEvent, SovereignEventBus


class TestSovereignEventBus:
    """Test async pub-sub and circular replay buffer."""

    def test_publish_and_subscribe(self) -> None:
        async def _run() -> None:
            bus = SovereignEventBus(buffer_size=10)
            sub_queue = await bus.subscribe()

            event = SovereignEvent(
                domain="SPACE",
                event_type="ORBITAL_SAR_PASS",
                corridor_id="ARCTIC-PASS-01",
                severity="CRITICAL",
                threat_score=0.85,
                title="Adversary Radar Satellite Overhead",
            )

            await bus.publish(event)
            received = await sub_queue.get()
            assert received.event_id == event.event_id
            assert received.domain == "SPACE"

            recent = bus.get_recent_events(limit=5)
            assert len(recent) == 1
            assert recent[0].title == "Adversary Radar Satellite Overhead"

            await bus.unsubscribe(sub_queue)

        asyncio.run(_run())


class TestStreamingAPI:
    """Test streaming event publish REST endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_publish_event_endpoint(self, client: TestClient) -> None:
        payload = {
            "domain": "MARITIME",
            "event_type": "DARK_FLEET_DETECTED",
            "corridor_id": "ST-LAWRENCE-SEAWAY",
            "severity": "CRITICAL",
            "threat_score": 0.9,
            "title": "Unidentified Vessel Without AIS Near Port",
        }
        resp = client.post("/v1/streaming/publish", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PUBLISHED"
        assert "event_id" in data
