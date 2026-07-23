from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from continuityos.compiler import ContinuityCompiler
from continuityos.domain import (
    AssertionClass,
    CompileRequest,
    ContinuityObjective,
    CorridorFactor,
    MetricName,
    MitigationAction,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.fusion import FusionEngine
from continuityos.graph import (
    DependencyEdge,
    DependencyEngine,
    DependencyGraph,
    DependencyNode,
    NodeType,
)


def provenance(uri: str) -> Provenance:
    body = uri.encode()
    return Provenance(
        uri=uri,
        content_sha256=hashlib.sha256(body).hexdigest(),
        licence="demonstration fixture; replace with signed snapshots",
    )


def public(metric: MetricName, value: float, assertion: AssertionClass, source: str) -> Observation:
    return Observation(
        source_id=source,
        source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        assertion_class=assertion,
        metric=metric,
        value=value,
        unit="normalized" if value <= 1 else "percent",
        observed_at=datetime.now(UTC),
        confidence=0.9,
        provenance=provenance(f"fixture://{source}/{metric.value}"),
    )


def operator(metric: MetricName, value: float, assertion: AssertionClass) -> Observation:
    return Observation(
        source_id="operator-telemetry",
        source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
        assertion_class=assertion,
        metric=metric,
        value=value,
        unit="days" if metric == MetricName.INVENTORY_DAYS else "ratio",
        observed_at=datetime.now(UTC),
        confidence=0.95,
        provenance=provenance(f"operator://demo/{metric.value}"),
    )


def main() -> None:
    observations = [
        public(MetricName.SEA_ICE_CONCENTRATION, 58, AssertionClass.ICE, "eccc-geomet"),
        public(MetricName.WIND_SEVERITY, 0.42, AssertionClass.WEATHER, "eccc-geomet"),
        operator(MetricName.PORT_AVAILABILITY, 0.75, AssertionClass.LIVE_AVAILABILITY),
        operator(MetricName.SATCOM_AVAILABILITY, 0.65, AssertionClass.LIVE_AVAILABILITY),
        operator(MetricName.CYBER_CONTROL_HEALTH, 0.55, AssertionClass.CYBER_HEALTH),
        operator(MetricName.DATA_INTEGRITY, 0.72, AssertionClass.CYBER_HEALTH),
        operator(MetricName.INSURANCE_AVAILABILITY, 0.6, AssertionClass.INSURANCE_ACCESS),
        operator(MetricName.ESCORT_CAPACITY, 0.35, AssertionClass.LIVE_CAPACITY),
        operator(MetricName.INVENTORY_DAYS, 16, AssertionClass.LIVE_CAPACITY),
    ]
    assessment = FusionEngine().assess("northwest-passage-demo", observations)
    actions = [
        MitigationAction(
            action_id="activate-secondary-satcom",
            name="Activate independently routed secondary SATCOM",
            cost=125_000,
            continuity_gain=0.19,
            risk_reductions={CorridorFactor.COMMUNICATIONS: 0.55},
            rationale="reduces communications provider and gateway concentration",
        ),
        MitigationAction(
            action_id="isolate-port-integration",
            name="Isolate suspect port integration and use validated offline manifests",
            cost=85_000,
            continuity_gain=0.15,
            risk_reductions={CorridorFactor.CYBER: 0.45, CorridorFactor.DATA_TRUST: 0.35},
            rationale="contains cyber trust failure without controlling port OT",
        ),
        MitigationAction(
            action_id="preposition-critical-inventory",
            name="Preposition fourteen days of critical inventory",
            cost=420_000,
            continuity_gain=0.28,
            risk_reductions={CorridorFactor.INVENTORY: 0.65},
            rationale="extends decision time and reduces emergency transport exposure",
        ),
        MitigationAction(
            action_id="reserve-alternate-port",
            name="Reserve alternate port and onward transport capacity",
            cost=610_000,
            continuity_gain=0.32,
            risk_reductions={CorridorFactor.PORT: 0.55, CorridorFactor.COMMERCIAL: 0.25},
            rationale="provides validated substitution rather than a map-only alternate",
        ),
    ]
    plan = ContinuityCompiler().compile(
        CompileRequest(
            assessment=assessment,
            objective=ContinuityObjective(
                minimum_continuity=0.65,
                maximum_shortage_days=5,
                maximum_recovery_days=30,
                budget=1_000_000,
            ),
            available_actions=actions,
        )
    )
    graph = DependencyGraph(
        graph_id="demo-cyber-physical-chain",
        nodes=[
            DependencyNode(
                node_id="shared-idp",
                name="Shared identity provider",
                node_type=NodeType.IDENTITY_PROVIDER,
                criticality=0.8,
                provider_id="provider-a",
            ),
            DependencyNode(
                node_id="manifest-api",
                name="Cargo manifest API",
                node_type=NodeType.CLOUD_SERVICE,
                criticality=0.85,
                provider_id="provider-a",
            ),
            DependencyNode(
                node_id="port-ot",
                name="Port operational technology boundary",
                node_type=NodeType.PORT_OT,
                criticality=0.95,
            ),
            DependencyNode(
                node_id="port",
                name="Northern port",
                node_type=NodeType.PORT,
                criticality=1.0,
            ),
            DependencyNode(
                node_id="community-fuel",
                name="Community fuel inventory",
                node_type=NodeType.INVENTORY,
                criticality=1.0,
            ),
        ],
        edges=[
            DependencyEdge(source="shared-idp", target="manifest-api", dependency_strength=0.95),
            DependencyEdge(source="manifest-api", target="port-ot", dependency_strength=0.75),
            DependencyEdge(source="port-ot", target="port", dependency_strength=0.95),
            DependencyEdge(source="port", target="community-fuel", dependency_strength=0.8),
        ],
    )
    blast_radius = DependencyEngine().analyze(graph, {"shared-idp"})
    print(
        json.dumps(
            {
                "assessment": assessment.model_dump(mode="json"),
                "plan": plan.model_dump(mode="json"),
                "dependency_impact": blast_radius.model_dump(mode="json"),
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
