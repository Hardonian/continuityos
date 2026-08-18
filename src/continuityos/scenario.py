"""Correlated failure scenario engine.

Traditional resilience software commonly assumes independent failures.
ContinuityOS explicitly models correlated failures — multiple events that
occur together and cascade through the dependency graph.

This engine is for DEFENSIVE planning only: resilience, continuity,
risk analysis, critical infrastructure protection, disaster recovery,
and logistics planning.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import CorridorState, Score
from continuityos.graph import DependencyEngine, DependencyGraph, GraphAssessment


class ScenarioEvent(BaseModel):
    """A single event in a correlated failure scenario."""

    target: str = Field(min_length=1, max_length=256)
    state: CorridorState
    description: str | None = None


class Scenario(BaseModel):
    """A set of correlated events for scenario simulation."""

    scenario_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    events: list[ScenarioEvent] = Field(min_length=1, max_length=200)
    duration_days: int = Field(default=30, ge=1, le=3650)
    description: str | None = None


class AffectedFacility(BaseModel):
    node_id: str
    impact_probability: Score
    reason: str


class PolicyViolation(BaseModel):
    check_id: str
    description: str
    severity: str


class ScenarioResult(BaseModel):
    """Result of simulating a correlated failure scenario."""

    result_id: UUID = Field(default_factory=uuid4)
    scenario_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    events_applied: int
    failed_nodes: list[str]
    graph_assessment: GraphAssessment | None = None
    remaining_viable_paths: int
    total_capacity_loss: Score
    affected_facilities: list[AffectedFacility]
    dependency_cascades: list[str]
    policy_violations: list[PolicyViolation]
    recovery_required: bool
    summary: str


def simulate_scenario(
    scenario: Scenario,
    graph: DependencyGraph,
    *,
    engine: DependencyEngine | None = None,
) -> ScenarioResult:
    """Simulate a correlated failure scenario against a dependency graph.

    This function is for defensive planning only. It does not generate
    offensive attack plans or vulnerability exploitation paths.
    """
    dep_engine = engine or DependencyEngine()
    node_ids = {node.node_id for node in graph.nodes}

    # Determine failed nodes from scenario events
    failed_nodes: set[str] = set()
    cascades: list[str] = []
    for event in scenario.events:
        if event.target in node_ids:
            if event.state in {
                CorridorState.FUNCTIONALLY_CLOSED,
                CorridorState.PHYSICALLY_CLOSED,
            }:
                failed_nodes.add(event.target)
                cascades.append(f"{event.target} → {event.state}")
        else:
            cascades.append(f"{event.target} → not in graph (external)")

    # Run dependency analysis if there are failed nodes
    assessment: GraphAssessment | None = None
    affected: list[AffectedFacility] = []
    if failed_nodes:
        assessment = dep_engine.analyze(graph, failed_nodes)
        for impact in assessment.impacted_nodes:
            if impact.node_id not in failed_nodes:
                affected.append(AffectedFacility(
                    node_id=impact.node_id,
                    impact_probability=impact.impact_probability,
                    reason=f"cascade from {' → '.join(impact.path)}",
                ))

    # Calculate remaining viable paths and capacity loss
    total_nodes = len(graph.nodes)
    affected_count = len(failed_nodes) + len(affected)
    capacity_loss = min(1.0, affected_count / total_nodes) if total_nodes > 0 else 0.0
    remaining_paths = max(0, total_nodes - affected_count)

    # Check for policy-like violations
    violations: list[PolicyViolation] = []
    if assessment:
        if assessment.single_points_of_failure:
            violations.append(PolicyViolation(
                check_id="SPOF_DETECTED",
                description=f"Single points of failure exposed: {', '.join(assessment.single_points_of_failure)}",
                severity="error",
            ))
        concentrated = {k: v for k, v in assessment.provider_concentration.items() if v >= 3}
        if concentrated:
            violations.append(PolicyViolation(
                check_id="PROVIDER_CONCENTRATION",
                description=f"Provider concentration risk: {concentrated}",
                severity="warning",
            ))

    recovery_required = capacity_loss > 0.1 or len(violations) > 0

    summary_parts = [
        f"{len(scenario.events)} events applied",
        f"{len(failed_nodes)} nodes directly failed",
        f"{len(affected)} downstream facilities affected",
        f"capacity loss: {capacity_loss:.1%}",
    ]
    if violations:
        summary_parts.append(f"{len(violations)} policy violations")

    return ScenarioResult(
        scenario_id=scenario.scenario_id,
        events_applied=len(scenario.events),
        failed_nodes=sorted(failed_nodes),
        graph_assessment=assessment,
        remaining_viable_paths=remaining_paths,
        total_capacity_loss=round(capacity_loss, 6),
        affected_facilities=affected,
        dependency_cascades=cascades,
        policy_violations=violations,
        recovery_required=recovery_required,
        summary="; ".join(summary_parts),
    )
