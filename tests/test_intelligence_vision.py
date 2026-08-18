from __future__ import annotations

import httpx
import pytest
from httpx import Response

from continuityos.intelligence import VisualIntelligenceEngine


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_visual_intelligence_engine_success(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = VisualIntelligenceEngine()

    class MockVLMClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url: str, json: dict) -> Response:
            return Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"threat_detected": true, "confidence": 0.92, '
                                    '"detected_objects": ["quadcopter", "jammer"], '
                                    '"visual_summary": "Hostile drone observed hovering over perimeter.", '
                                    '"corridor_impact_factor": "ESCORT", '
                                    '"recommended_action": "Deploy C-UAS directional jammer."}'
                                )
                            }
                        }
                    ]
                },
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", MockVLMClient)

    analysis = await engine.analyze_frame("drone-stream-01", "aW1hZ2VkYXRh")
    assert analysis.stream_id == "drone-stream-01"
    assert analysis.threat_detected is True
    assert analysis.confidence == 0.92
    assert "quadcopter" in analysis.detected_objects
    assert analysis.corridor_impact_factor == "ESCORT"


@pytest.mark.anyio
async def test_visual_intelligence_engine_fallback_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = VisualIntelligenceEngine()

    class MockFailingClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url: str, json: dict) -> Response:
            raise httpx.ConnectError("Connection refused by local VLM")

    monkeypatch.setattr(httpx, "AsyncClient", MockFailingClient)

    analysis = await engine.analyze_frame("drone-stream-02", "aW1hZ2VkYXRh")
    assert analysis.stream_id == "drone-stream-02"
    assert analysis.threat_detected is False
    assert analysis.confidence == 0.5
    assert "optical flow nominal" in analysis.visual_summary
