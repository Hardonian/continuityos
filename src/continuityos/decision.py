from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.compiler import ContinuityCompiler
from continuityos.domain import (
    CompiledPlan,
    CompileRequest,
    ContinuityObjective,
    CorridorAssessment,
    MitigationAction,
    Observation,
)
from continuityos.exchange import ExchangeManifest
from continuityos.fusion import FusionEngine
from continuityos.graph import DependencyEngine, DependencyGraph, GraphAssessment


class DecisionPacketRequest(BaseModel):
    """Single-call, explainable assessment → impact → mitigation request."""

    corridor_id: str = Field(min_length=1, max_length=128)
    observations: list[Observation] = Field(min_length=1, max_length=512)
    as_of: datetime | None = None
    graph: DependencyGraph
    failed_nodes: list[str] = Field(min_length=1, max_length=256)
    objective: ContinuityObjective
    available_actions: list[MitigationAction] = Field(max_length=24)


class DecisionPacket(BaseModel):
    """Portable decision artifact; never executes actions or grants authority."""

    contract_version: str = "continuityos.decision-packet.v1"
    packet_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    corridor_id: str
    assessment: CorridorAssessment
    dependency_assessment: GraphAssessment
    plan: CompiledPlan
    evidence_manifest: ExchangeManifest
    approval_required: bool
    human_action_boundary: str = (
        "Plan generation is advisory only. A human operator must review and approve "
        "any consequential action; ContinuityOS does not execute or dispatch actions."
    )


def build_decision_packet(
    request: DecisionPacketRequest,
    *,
    fusion: FusionEngine,
    dependency_engine: DependencyEngine,
    compiler: ContinuityCompiler,
    evidence_manifest: ExchangeManifest,
) -> DecisionPacket:
    assessment = fusion.assess(
        request.corridor_id,
        request.observations,
        as_of=request.as_of,
    )
    dependency_assessment = dependency_engine.analyze(
        request.graph,
        set(request.failed_nodes),
    )
    plan = compiler.compile(
        CompileRequest(
            assessment=assessment,
            objective=request.objective,
            available_actions=request.available_actions,
        )
    )
    return DecisionPacket(
        corridor_id=request.corridor_id,
        assessment=assessment,
        dependency_assessment=dependency_assessment,
        plan=plan,
        evidence_manifest=evidence_manifest,
        approval_required=plan.approval_required,
    )
