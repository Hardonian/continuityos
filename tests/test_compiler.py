from __future__ import annotations

from continuityos.compiler import ContinuityCompiler
from continuityos.domain import (
    CompileRequest,
    ContinuityObjective,
    CorridorAssessment,
    CorridorFactor,
    CorridorState,
    FactorAssessment,
    MitigationAction,
)


def test_compiler_selects_lowest_cost_objective_meeting_plan() -> None:
    assessment = CorridorAssessment(
        corridor_id="test",
        overall_risk=0.55,
        confidence=0.9,
        state=CorridorState.DEGRADED,
        factors=[],
        missing_required_metrics=[],
        caveats=[],
    )
    actions = [
        MitigationAction(
            action_id="a-secondary-satcom",
            name="Activate secondary SATCOM",
            cost=100,
            continuity_gain=0.35,
            rationale="reduces communications concentration",
        ),
        MitigationAction(
            action_id="b-preposition",
            name="Preposition critical inventory",
            cost=90,
            continuity_gain=0.31,
            rationale="extends buffer",
        ),
        MitigationAction(
            action_id="c-premium-airlift",
            name="Reserve emergency airlift",
            cost=500,
            continuity_gain=0.70,
            rationale="high-cost fallback",
        ),
    ]
    request = CompileRequest(
        assessment=assessment,
        objective=ContinuityObjective(minimum_continuity=0.75, budget=250),
        available_actions=actions,
    )
    plan = ContinuityCompiler().compile(request)
    assert plan.objective_met
    assert plan.total_cost == 190
    assert [action.action_id for action in plan.selected_actions] == [
        "a-secondary-satcom",
        "b-preposition",
    ]


def test_compiler_honors_prerequisites() -> None:
    assessment = CorridorAssessment(
        corridor_id="test",
        overall_risk=0.5,
        confidence=0.8,
        state=CorridorState.DEGRADED,
        factors=[],
        missing_required_metrics=[],
        caveats=[],
    )
    dependent = MitigationAction(
        action_id="switch-provider",
        name="Switch provider",
        cost=20,
        continuity_gain=0.4,
        prerequisites={"validate-terminal"},
        rationale="requires validation",
    )
    request = CompileRequest(
        assessment=assessment,
        objective=ContinuityObjective(minimum_continuity=0.8, budget=100),
        available_actions=[dependent],
    )
    plan = ContinuityCompiler().compile(request)
    assert not plan.objective_met
    assert plan.selected_actions == []


def test_factor_reduction_is_applied_to_matching_factor_only() -> None:
    assessment = CorridorAssessment(
        corridor_id="factor-test",
        overall_risk=0.5,
        confidence=0.9,
        state=CorridorState.DEGRADED,
        factors=[
            FactorAssessment(
                factor=CorridorFactor.COMMUNICATIONS,
                risk=0.8,
                confidence=0.9,
                evidence_ids=[],
                rationale="test",
            ),
            FactorAssessment(
                factor=CorridorFactor.PORT,
                risk=0.2,
                confidence=0.9,
                evidence_ids=[],
                rationale="test",
            ),
        ],
        missing_required_metrics=[],
        caveats=[],
    )
    action = MitigationAction(
        action_id="port-only",
        name="Improve port resilience",
        cost=10,
        continuity_gain=0.9,
        risk_reductions={CorridorFactor.PORT: 0.5},
        rationale="must not reduce unrelated communications risk",
    )
    plan = ContinuityCompiler().compile(
        CompileRequest(
            assessment=assessment,
            objective=ContinuityObjective(minimum_continuity=0.55, budget=20),
            available_actions=[action],
        )
    )
    assert plan.projected_continuity < 0.6
