from datetime import UTC, datetime

import pytest
from httpx import Response

from continuityos.decision import DecisionPacket
from continuityos.domain import CompiledPlan, CorridorAssessment, CorridorState, MitigationAction
from continuityos.exchange import ExchangeManifest
from continuityos.graph import GraphAssessment
from continuityos.intelligence import AgenticIntelligenceEngine


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_intelligence_briefing_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = AgenticIntelligenceEngine()

    class MockClient:
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
                                    '{"executive_summary": "Test Summary", '
                                    '"strategic_implications": "Test Imp", '
                                    '"advisory_actions": ["Act 1"]}'
                                )
                            }
                        }
                    ]
                },
                request=httpx.Request("POST", url),
            )

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    packet = DecisionPacket(
        corridor_id="NATO-CORR-1",
        assessment=CorridorAssessment(
            corridor_id="NATO-CORR-1",
            overall_risk=0.8,
            confidence=0.9,
            state=CorridorState.FUNCTIONALLY_CLOSED,
            factors=[],
            missing_required_metrics=[],
            caveats=[],
        ),
        dependency_assessment=GraphAssessment(
            graph_id="g1",
            nodes_analyzed=1,
            failed_nodes=["n1"],
            impacted_nodes=[],
            max_blast_radius=1,
            total_risk_score=0.8,
            total_weighted_impact=0.8,
            provider_concentration={},
            single_points_of_failure=[],
        ),
        plan=CompiledPlan(
            assessment_id="00000000-0000-0000-0000-000000000000",
            selected_actions=[
                MitigationAction(
                    action_id="act-1",
                    name="prov-1",
                    action_type="RESERVE_DRAWDOWN",
                    cost=100.0,
                    continuity_gain=0.5,
                    rationale="Test",
                )
            ],
            projected_risk=0.1,
            projected_continuity=0.95,
            total_cost=100.0,
            objective_met=True,
            deterministic_solver="Test",
            approval_required=True,
        ),
        evidence_manifest=ExchangeManifest(
            generated_at=datetime.now(UTC),
            record_count=0,
            record_hashes=[],
            content_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            limitations=[],
        ),
        approval_required=True,
    )

    briefing = await engine.generate_briefing(packet)
    assert briefing.executive_summary == "Test Summary"
    assert len(briefing.advisory_actions) == 1
