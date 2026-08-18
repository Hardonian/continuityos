import pytest
from httpx import Response
from continuityos.decision import DecisionPacket
from continuityos.domain import CorridorAssessment, CompiledPlan, MitigationAction, CorridorState
from continuityos.graph import GraphAssessment
from continuityos.exchange import ExchangeManifest
from continuityos.intelligence import AgenticIntelligenceEngine


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"

@pytest.mark.anyio
async def test_intelligence_briefing_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = AgenticIntelligenceEngine()
    
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        
        async def post(self, url: str, json: dict) -> Response:
            return Response(200, json={
                "choices": [{
                    "message": {
                        "content": (
                            '{"executive_summary": "Test Summary", '
                            '"strategic_implications": "Test Imp", '
                            '"advisory_actions": ["Act 1"]}'
                        )
                    }
                }]
            })

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
            caveats=[]
        ),
        dependency_assessment=GraphAssessment(
            graph_id="g1",
            nodes_analyzed=1,
            failed_nodes=["n1"],
            impacted_nodes=[],
            max_blast_radius=1,
            total_risk_score=0.8
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
                    rationale="Test"
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
            manifest_id="00000000-0000-0000-0000-000000000000",
            created_by="test",
            records=[]
        ),
        approval_required=True
    )
    
    briefing = await engine.generate_briefing(packet)
    assert briefing.executive_summary == "Test Summary"
    assert len(briefing.advisory_actions) == 1
