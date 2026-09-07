"""Tests verifying the 10 Core Invariants of ContinuityOS v1.0.

Invariants:
1. Physical availability is not equivalent to effective availability.
2. UNKNOWN must never silently become HEALTHY.
3. All externally derived operational state must preserve provenance.
4. All policy evaluation must be deterministic given identical input.
5. A failed external provider must degrade gracefully.
6. Every effective-state decision must be explainable.
7. Correlated failures must be explicitly representable.
8. Recovery is separate from reopening.
9. Nominal redundancy must be tested for shared upstream dependencies.
10. Continuity policies must be machine-readable, versionable, portable, testable, and auditable.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from continuityos.closure import ClosureInput, assess_closure
from continuityos.domain import (
    CorridorState,
    MetricName,
    Observation,
)
from continuityos.dsl import load_resource, validate_resource
from continuityos.evidence import EvidenceLedger
from continuityos.graph import DependencyEdge, DependencyGraph, DependencyNode
from continuityos.independence import ProviderIndependenceAnalyzer
from continuityos.policy import (
    ContinuityPolicy,
    ObservedState,
    PolicyAssertion,
    PolicyRule,
    evaluate_policy,
)
from continuityos.recovery import RecoveryProfile, model_recovery
from continuityos.scenario import Scenario, ScenarioEvent, simulate_scenario


class TestV1CoreInvariants:
    def test_invariant_1_physical_not_equal_effective_availability(self) -> None:
        """Invariant 1: Physical availability is not equivalent to effective availability.

        A corridor may be physically clear, but if marine war-risk underwriters cancel
        coverage or container carriers divert fleets, effective state is functionally closed.
        """
        closure_input = ClosureInput(
            resource_ref="corridor/primary",
            physically_accessible=True,
            insurance_available=False,
            insurance_coverage=0.0,
            navigation_trust_score=0.90,
            operator_confidence=0.85,
            navigation_state="healthy",
            carrier_capacity_state="unavailable",
        )
        assessment = assess_closure(closure_input)

        assert assessment.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
        assert "uninsurable" in assessment.reason_codes
        comp = assessment.to_composite_state()
        assert comp.physical_state.value == "open"
        assert comp.commercial_state.insurance == "uninsurable"
        assert comp.effective_state.value == "open_but_uninsurable"

    def test_invariant_2_unknown_never_silently_becomes_healthy(self) -> None:
        """Invariant 2: UNKNOWN must never silently become HEALTHY.

        When observations are missing or untrusted, the system must report UNKNOWN
        or fail policy assertions, never defaulting to compliant/healthy.
        """
        # A closure input with zero observations or complete unknown telemetry
        closure_input = ClosureInput(
            resource_ref="corridor/dark-corridor",
            physically_accessible=False,  # unknown/inaccessible
            navigation_trust_score=0.0,
            operator_confidence=0.0,
            navigation_state="unknown",
            carrier_capacity_state="unknown",
        )
        assessment = assess_closure(closure_input)
        assert assessment.effective_state in {
            CorridorState.PHYSICALLY_CLOSED,
            CorridorState.UNKNOWN,
        }
        assert assessment.effective_state != CorridorState.OPEN

        # Policy assertion against unknown state
        policy = ContinuityPolicy(
            policy_id="test-unknown",
            version="1.0",
            rules=[
                PolicyRule(
                    rule_id="RULE-UNKNOWN-CHECK",
                    description="Require verified navigation trust",
                    assertion=PolicyAssertion(minimum_trust_score=0.80),
                ),
            ],
        )
        state_unknown = ObservedState(trust_scores={})
        res = evaluate_policy(policy, state_unknown)
        assert res.compliant is False
        assert len(res.violations) == 1
        assert (
            "missing" in res.violations[0].deficit.lower()
            or "unknown" in res.violations[0].observed.lower()
        )

    def test_invariant_3_provenance_preservation(self, tmp_path: Path) -> None:
        """Invariant 3: All externally derived operational state must preserve provenance.

        Every observation must maintain source, retrieved timestamp, confidence,
        and append-only cryptographic evidence ledger trail.
        """
        from datetime import UTC, datetime

        from continuityos.domain import AssertionClass, Provenance, SourceTrust

        obs = Observation(
            observation_id=uuid4(),
            source_id="sar-satellite-01",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.EARTH_OBSERVATION,
            metric=MetricName.AIS_TRAFFIC_INDEX,
            value=0.82,
            unit="ratio",
            observed_at=datetime.now(UTC),
            confidence=0.92,
            provenance=Provenance(
                uri="urn:satellite:sar-01",
                content_sha256="a" * 64,
            ),
        )
        assert obs.source_id == "sar-satellite-01"
        assert obs.observed_at is not None
        assert obs.confidence == 0.92

        ledger_file = tmp_path / "ledger.jsonl"
        ledger = EvidenceLedger(ledger_file)
        rec = ledger.append("OBSERVATION", "obs-001", obs.model_dump(mode="json"))
        assert rec.record_hash is not None
        assert rec.previous_hash is not None

        # Verify integrity
        errors = ledger.verify()
        assert len(errors) == 0

    def test_invariant_4_policy_evaluation_deterministic(self) -> None:
        """Invariant 4: All policy evaluation must be deterministic given identical input."""
        policy = ContinuityPolicy(
            policy_id="test-pol",
            version="1.0",
            rules=[
                PolicyRule(
                    rule_id="COMM-001",
                    description="2 independent comms",
                    assertion=PolicyAssertion(minimum_providers=2),
                ),
                PolicyRule(
                    rule_id="INV-001",
                    description="30 days reserve",
                    assertion=PolicyAssertion(minimum_reserve_days=30),
                ),
            ],
        )
        state = ObservedState(
            provider_counts={"satcom": 1},
            reserve_days={"fuel": 25.0},
            overall_continuity=0.85,
        )

        res1 = evaluate_policy(policy, state)
        res2 = evaluate_policy(policy, state)
        assert res1.compliant == res2.compliant
        assert len(res1.violations) == len(res2.violations)
        assert [v.rule_id for v in res1.violations] == [v.rule_id for v in res2.violations]

    def test_invariant_5_graceful_degradation_on_provider_failure(self) -> None:
        """Invariant 5: A failed external provider must degrade gracefully."""
        graph = DependencyGraph(
            graph_id="provider-resilience-net",
            nodes=[
                DependencyNode(
                    node_id="comms_satcom_a",
                    name="SATCOM Primary",
                    node_type="satcom",
                    criticality=0.8,
                ),
                DependencyNode(
                    node_id="comms_satcom_b",
                    name="SATCOM Secondary",
                    node_type="satcom",
                    criticality=0.7,
                ),
                DependencyNode(
                    node_id="corridor_main",
                    name="Main Corridor",
                    node_type="corridor",
                    criticality=0.9,
                ),
            ],
            edges=[
                DependencyEdge(
                    source="comms_satcom_a",
                    target="corridor_main",
                    dependency_strength=0.8,
                    substitutable=True,
                ),
                DependencyEdge(
                    source="comms_satcom_b",
                    target="corridor_main",
                    dependency_strength=0.7,
                    substitutable=True,
                ),
            ],
        )
        # Fail primary SATCOM provider
        scenario = Scenario(
            scenario_id="scen-provider-loss",
            name="Primary SATCOM Outage",
            events=[ScenarioEvent(target="comms_satcom_a", state=CorridorState.PHYSICALLY_CLOSED)],
            duration_days=7,
        )
        result = simulate_scenario(scenario, graph)
        assert "comms_satcom_a" in result.failed_nodes
        # Corridor should still be viable because secondary satcom is substitutable
        assert "corridor_main" not in result.failed_nodes

    def test_invariant_6_explainable_decisions(self) -> None:
        """Invariant 6: Every effective-state decision must be explainable."""
        closure_input = ClosureInput(
            resource_ref="corridor/trans-arctic",
            physically_accessible=True,
            insurance_available=False,
            insurance_coverage=0.0,
            navigation_trust_score=0.40,
            operator_confidence=0.50,
            navigation_state="degraded",
            carrier_capacity_state="unavailable",
        )
        assessment = assess_closure(closure_input)
        explanation = assessment.explain()

        assert "[PHYSICAL]" in explanation
        assert "[OPERATIONAL]" in explanation
        assert "[COMMERCIAL]" in explanation
        assert "Effective State:" in explanation
        assert len(assessment.reason_codes) > 0

    def test_invariant_7_correlated_failures_explicitly_representable(self) -> None:
        """Invariant 7: Correlated failures must be explicitly representable."""
        scen = Scenario(
            scenario_id="scen-correlated-chokepoints",
            name="Simultaneous Hormuz and Red Sea and LEO disruption",
            events=[
                ScenarioEvent(target="corridor_hormuz", state=CorridorState.FUNCTIONALLY_CLOSED),
                ScenarioEvent(target="corridor_red_sea", state=CorridorState.OPEN_DEGRADED),
                ScenarioEvent(
                    target="satcom_commercial_leo", state=CorridorState.PHYSICALLY_CLOSED
                ),
            ],
            duration_days=14,
        )
        assert len(scen.events) == 3
        assert scen.events[0].target == "corridor_hormuz"
        assert scen.events[1].target == "corridor_red_sea"
        assert scen.events[2].target == "satcom_commercial_leo"

    def test_invariant_8_recovery_separate_from_reopening(self) -> None:
        """Invariant 8: Recovery is separate from reopening.

        Route reopened != network healthy. Backlog, vessel repositioning,
        and inventory replenishment lag must clear before full health.
        """
        profile = RecoveryProfile(
            resource_ref="corridor/st-lawrence",
            incident_description="Winter freeze blockage",
            physical_reopening_days=10,
            port_backlog_days=14,
            insurance_normalization_days=20,
            carrier_return_days=25,
            inventory_replenishment_days=35,
            full_restoration_days=45,
        )
        # At day 12: physical route is open, but system is still lagging and NOT healthy
        timeline_day12 = model_recovery(profile, days_since_incident=12)
        assert timeline_day12.reopened_but_not_healthy is True
        assert timeline_day12.is_healthy is False

        # At day 50: still lagging (T3/T4 recovery in progress)
        timeline_day50 = model_recovery(profile, days_since_incident=50)
        assert timeline_day50.is_healthy is False

        # After total recovery days: full health restored
        timeline_restored = model_recovery(
            profile, days_since_incident=timeline_day12.total_recovery_days + 1
        )
        assert timeline_restored.is_healthy is True

    def test_invariant_9_nominal_redundancy_tested_for_shared_upstream(self) -> None:
        """Invariant 9: Nominal redundancy must be tested for shared upstream dependencies.

        Two SATCOM systems that share a common downlink teleport or backhaul must be
        flagged as false redundancy.
        """
        graph = DependencyGraph(
            graph_id="redundancy-test",
            nodes=[
                DependencyNode(
                    node_id="gateway_teleport_arctic",
                    name="Shared Teleport",
                    node_type="satellite_uplink",
                ),
                DependencyNode(
                    node_id="satcom_provider_1", name="Provider Alpha", node_type="satcom"
                ),
                DependencyNode(
                    node_id="satcom_provider_2", name="Provider Bravo", node_type="satcom"
                ),
                DependencyNode(
                    node_id="terminal_hq", name="Operations Center", node_type="facility"
                ),
            ],
            edges=[
                DependencyEdge(source="gateway_teleport_arctic", target="satcom_provider_1"),
                DependencyEdge(source="gateway_teleport_arctic", target="satcom_provider_2"),
                DependencyEdge(source="satcom_provider_1", target="terminal_hq"),
                DependencyEdge(source="satcom_provider_2", target="terminal_hq"),
            ],
        )
        analyzer = ProviderIndependenceAnalyzer(graph)
        result = analyzer.analyze_category(
            graph, "satcom", ["satcom_provider_1", "satcom_provider_2"]
        )
        assert result.declared_count == 2
        assert result.independent_count == 1
        assert result.redundancy_valid is False
        assert len(result.shared_dependencies) >= 1
        assert result.shared_dependencies[0].dependency_id == "gateway_teleport_arctic"

    def test_invariant_10_machine_readable_versionable_auditable_policy(self) -> None:
        """Invariant 10: Continuity policies must be machine-readable, versionable, portable, testable, and auditable."""
        yaml_content = Path("examples/arctic/policy.yaml")
        assert yaml_content.exists()
        resource = load_resource(yaml_content)
        assert resource.api_version == "continuity.io/v1"
        assert resource.kind.value == "ContinuityPolicy"
        errors = validate_resource(resource)
        assert len(errors) == 0
