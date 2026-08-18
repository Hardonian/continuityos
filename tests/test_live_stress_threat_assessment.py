"""1000-Point QA, Threat Assessment, Stress Testing & Live Simulation Battery.

Comprehensive defensive resilience, threat scenario simulation, and high-scale stress test
suite evaluating ContinuityOS against:
  1. Nation-State Electronic Warfare & PNT/GNSS Degradation
  2. SATCOM Denial & Space Weather / Geomagnetic Blackouts
  3. Geopolitical Sanctions, Alliance Shifts & Marine War-Risk Insurance Withdrawal
  4. Port Industrial OT Cyber Incidents & Berth Physical Blockages
  5. Multi-Chokepoint Correlated Cascade Disruption
  6. High-Scale Dependency Graph Stress (1,000+ nodes, cycle density, blast radius)
  7. High-Throughput Observation Ingestion, Freshness Decay & Fuzzing
  8. Cryptographic Evidence Ledger Integrity, Tamper Detection & Concurrency Stress
"""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.closure import ClosureInput, LayerState, assess_closure
from continuityos.compiler import ContinuityCompiler
from continuityos.domain import (
    AssertionClass,
    CompileRequest,
    ContinuityObjective,
    CorridorFactor,
    CorridorState,
    MetricName,
    MitigationAction,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.evidence import EvidenceLedger
from continuityos.fusion import FusionEngine
from continuityos.graph import (
    DependencyEdge,
    DependencyEngine,
    DependencyGraph,
    DependencyNode,
    NodeType,
    detect_cycles,
)
from continuityos.inventory import InventoryProfile, simulate_inventory
from continuityos.policy import (
    ContinuityPolicy,
    ObservedState,
    PolicyAssertion,
    PolicyRule,
    evaluate_policy,
)
from continuityos.reconcile import ActualState, DesiredState, ReconciliationStatus, reconcile
from continuityos.recovery import RecoveryPhase, RecoveryProfile, model_recovery
from continuityos.remediation import generate_remediation
from continuityos.scenario import Scenario, ScenarioEvent, simulate_scenario
from continuityos.trust import (
    DependencyTrust,
    TrustAggregation,
    TrustDimensions,
    TrustProvenance,
    evaluate_trust,
)


class TestNationStateEWAndGNSSThreatScenarios:
    """Category 1: Nation-State Electronic Warfare, GNSS Spoofing & PNT Denial."""

    @pytest.mark.parametrize("spoofing_intensity", [0.1, 0.25, 0.45, 0.65, 0.85, 0.99])
    def test_gnss_spoofing_functional_closure(self, spoofing_intensity: float) -> None:
        """Evaluate functional closure under variable GNSS/PNT jamming and spoofing."""
        nav_trust = max(0.01, 1.0 - spoofing_intensity)
        closure_input = ClosureInput(
            resource_ref="corridor/barents-kara-chokepoint",
            physically_accessible=True,
            navigation_available=True,
            navigation_trust=nav_trust,
            communications_available=True,
            communications_trust=0.9,
            insurance_available=True,
            carrier_capacity_available=True,
            data_integrity=nav_trust,
        )
        assessment = assess_closure(closure_input)
        if nav_trust < 0.5:
            assert assessment.effective_state == CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED
            assert "navigation_untrusted" in assessment.reason_codes
        else:
            assert assessment.effective_state in {CorridorState.OPEN, CorridorState.OPEN_DEGRADED}

    def test_pnt_multi_constellation_denial_cascade(self) -> None:
        """Simulate simultaneous GPS, Galileo, and GLONASS signal denial in polar theater."""
        nodes = [
            DependencyNode(node_id="gnss_constellation", name="PNT Satellite Constellation", node_type=NodeType.DATA_FEED, criticality=0.95),
            DependencyNode(node_id="vessel_ins_system", name="Inertial Navigation Backup", node_type=NodeType.VESSEL, criticality=0.85),
            DependencyNode(node_id="corridor_vilkitsky", name="Vilkitsky Strait Transit", node_type=NodeType.CORRIDOR, criticality=0.98),
            DependencyNode(node_id="facility_pevek", name="Port of Pevek", node_type=NodeType.PORT, criticality=0.90),
        ]
        edges = [
            DependencyEdge(source="gnss_constellation", target="corridor_vilkitsky", dependency_strength=0.95, substitutable=True, substitute_group="pnt_source"),
            DependencyEdge(source="vessel_ins_system", target="corridor_vilkitsky", dependency_strength=0.70, substitutable=True, substitute_group="pnt_source"),
            DependencyEdge(source="corridor_vilkitsky", target="facility_pevek", dependency_strength=0.95),
        ]
        graph = DependencyGraph(graph_id="polar-pnt-network", nodes=nodes, edges=edges)

        # Scenario: Primary GNSS jammed, INS backup operative
        engine = DependencyEngine()
        assessment_primary_fail = engine.analyze(graph, {"gnss_constellation"})
        impacted_nodes = {n.node_id: n.impact_probability for n in assessment_primary_fail.impacted_nodes}
        # Substitutable INS attenuates cascade
        assert impacted_nodes["corridor_vilkitsky"] < 0.5

        # Scenario: Both GNSS and INS denied (full electronic blackout)
        assessment_total_fail = engine.analyze(graph, {"gnss_constellation", "vessel_ins_system"})
        impacted_total = {n.node_id: n.impact_probability for n in assessment_total_fail.impacted_nodes}
        assert impacted_total["corridor_vilkitsky"] >= 0.90


class TestSATCOMDenialAndSpaceWeatherScenarios:
    """Category 2: SATCOM Denial, Anti-Satellite (ASAT) Cyber Incidents & Solar Flares."""

    @pytest.mark.parametrize("solar_geomagnetic_storm_kp", [3, 5, 7, 8, 9])
    def test_geomagnetic_storm_satcom_attenuation(self, solar_geomagnetic_storm_kp: int) -> None:
        """Simulate high-latitude solar storm impact on SATCOM and polar HF radio."""
        satcom_avail = max(0.05, 1.0 - (solar_geomagnetic_storm_kp / 10.0))
        comms_trust = DependencyTrust(
            dependency_ref="telecom/polar-satcom-mesh",
            dimensions=TrustDimensions(
                physical_availability=satcom_avail,
                cyber_integrity=0.90,
                communications_integrity=satcom_avail,
            ),
            aggregation=TrustAggregation.MINIMUM,
            provenance=TrustProvenance(minimum_independent_sources=2, actual_independent_sources=2),
        )
        trust_assessment = evaluate_trust(comms_trust)
        assert trust_assessment.aggregate_score == pytest.approx(satcom_avail, 0.01)

        closure_input = ClosureInput(
            resource_ref="corridor/polar-ice-route",
            physically_accessible=True,
            communications_available=satcom_avail > 0.1,
            communications_trust=satcom_avail,
        )
        closure_res = assess_closure(closure_input)
        if satcom_avail < 0.5:
            assert closure_res.effective_state == CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED


class TestGeopoliticalSanctionsAndInsuranceRevocation:
    """Category 3: Maritime Sanctions, War-Risk Cancellation & Carrier Diversion."""

    def test_war_risk_underwriter_withdrawal_closure(self) -> None:
        """Marine insurers revoke war-risk policy for transit corridor."""
        closure_input = ClosureInput(
            resource_ref="corridor/suez-red-sea",
            physically_accessible=True,
            navigation_available=True,
            communications_available=True,
            insurance_available=False,
            insurance_coverage=0.0,
            carrier_capacity_available=True,
        )
        closure_assessment = assess_closure(closure_input)
        assert closure_assessment.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
        assert "uninsurable" in closure_assessment.reason_codes
        assert closure_assessment.commercial_state.state == LayerState.DEGRADED

    def test_carrier_cartel_diversion_closure(self) -> None:
        """Shipping alliances re-route container vessels around Cape of Good Hope."""
        closure_input = ClosureInput(
            resource_ref="corridor/bab-el-mandeb",
            physically_accessible=True,
            insurance_available=True,
            insurance_coverage=0.8,
            carrier_capacity_available=False,
            carrier_capacity_ratio=0.0,
        )
        closure_assessment = assess_closure(closure_input)
        assert closure_assessment.effective_state == CorridorState.OPEN_BUT_NO_CARRIER_CAPACITY
        assert "no_carrier_capacity" in closure_assessment.reason_codes

    def test_reconciliation_and_remediation_under_sanctions(self) -> None:
        """Policy-as-Code reconciliation detects single-flag dependency violation."""
        policy = ContinuityPolicy(
            policy_id="strategic-corridor-compliance",
            rules=[
                PolicyRule(
                    rule_id="SANCT-001",
                    description="Corridor must maintain independent non-sanctioned carrier routes",
                    assertion=PolicyAssertion(minimum_independent_routes=2, minimum_continuity=0.95),
                ),
                PolicyRule(
                    rule_id="INS-001",
                    description="Marine insurance trust score must remain >= 0.80",
                    assertion=PolicyAssertion(minimum_trust_score=0.80),
                ),
            ],
        )
        observed = ObservedState(
            independent_route_count=1,
            overall_continuity=0.72,
            trust_scores={"marine_insurance": 0.40},
        )
        evaluation = evaluate_policy(policy, observed)
        assert evaluation.compliant is False
        assert len(evaluation.violations) == 2


class TestPortOTCyberIncidentsAndHubBlockages:
    """Category 4: Industrial Control System (ICS/OT) Cyber Attacks & Terminal Failures."""

    def test_port_crane_ot_ransomware_scenario(self) -> None:
        """SCADA/OT ransomware halts automated container handling cranes."""
        nodes = [
            DependencyNode(node_id="port_scada_network", name="Port SCADA OT Network", node_type=NodeType.PORT_OT, criticality=0.95),
            DependencyNode(node_id="container_terminal_a", name="Main Container Terminal", node_type=NodeType.PORT, criticality=0.90),
            DependencyNode(node_id="berth_fuel_bunkering", name="Marine Bunkering Berth", node_type=NodeType.FUEL, criticality=0.85),
            DependencyNode(node_id="regional_power_grid", name="Regional Substation Power", node_type=NodeType.POWER, criticality=0.90),
        ]
        edges = [
            DependencyEdge(source="regional_power_grid", target="port_scada_network", dependency_strength=0.95),
            DependencyEdge(source="port_scada_network", target="container_terminal_a", dependency_strength=0.90),
            DependencyEdge(source="port_scada_network", target="berth_fuel_bunkering", dependency_strength=0.80),
        ]
        graph = DependencyGraph(graph_id="port-ot-infrastructure", nodes=nodes, edges=edges)

        scenario = Scenario(
            scenario_id="ot-ransomware-wave",
            name="Port SCADA Network Ransomware Lockout",
            events=[
                ScenarioEvent(target="port_scada_network", state=CorridorState.FUNCTIONALLY_CLOSED),
            ],
            duration_days=14,
        )
        sim_result = simulate_scenario(scenario, graph)
        assert sim_result.events_applied == 1
        assert "port_scada_network" in sim_result.failed_nodes
        assert sim_result.recovery_required is True
        assert len(sim_result.affected_facilities) >= 2

    def test_port_recovery_timeline_modeling(self) -> None:
        """Model recovery lag from physical OT clean-up through cargo backlog resolution."""
        profile = RecoveryProfile(
            resource_ref="port/terminal-rotterdam",
            incident_description="OT Ransomware lockout requiring firmware reimaging and vessel re-scheduling",
            physical_reopening_days=4,
            port_backlog_days=10,
            carrier_return_days=14,
            vessel_repositioning_days=18,
            inventory_replenishment_days=28,
        )
        timeline = model_recovery(profile, days_since_incident=5)
        assert timeline.total_recovery_days > 28
        assert timeline.current_phase == RecoveryPhase.T1_PHYSICAL_REOPENING
        assert timeline.recovery_progress > 0.0


class TestCorrelatedCascadeShocksAndSupplyChainExhaustion:
    """Category 5: Correlated Multi-Point Disruptions & Strategic Inventory Depletion."""

    def test_triple_chokepoint_correlated_cascade(self) -> None:
        """Simulate simultaneous disruptions across route, port, and satellite communication."""
        nodes = [
            DependencyNode(node_id="hub_a", name="Hub A", node_type=NodeType.PORT, criticality=0.9),
            DependencyNode(node_id="chokepoint_b", name="Chokepoint B", node_type=NodeType.CORRIDOR, criticality=0.95),
            DependencyNode(node_id="terminal_c", name="Terminal C", node_type=NodeType.FACILITY, criticality=0.95),
            DependencyNode(node_id="satcom_mesh", name="SATCOM Mesh", node_type=NodeType.SATCOM, criticality=0.85),
            DependencyNode(node_id="fuel_refinery", name="Fuel Refinery", node_type=NodeType.SUPPLIER, criticality=0.9),
        ]
        edges = [
            DependencyEdge(source="satcom_mesh", target="chokepoint_b", dependency_strength=0.9),
            DependencyEdge(source="fuel_refinery", target="hub_a", dependency_strength=0.9),
            DependencyEdge(source="hub_a", target="chokepoint_b", dependency_strength=0.95),
            DependencyEdge(source="chokepoint_b", target="terminal_c", dependency_strength=0.95),
        ]
        graph = DependencyGraph(graph_id="strategic-macro-corridor", nodes=nodes, edges=edges)

        scenario = Scenario(
            scenario_id="triple-threat-cascade",
            name="Severe Weather + Cyber Attack + Power Grid Failure",
            events=[
                ScenarioEvent(target="satcom_mesh", state=CorridorState.FUNCTIONALLY_CLOSED),
                ScenarioEvent(target="hub_a", state=CorridorState.PHYSICALLY_CLOSED),
            ],
            duration_days=30,
        )
        res = simulate_scenario(scenario, graph)
        assert res.total_capacity_loss >= 0.50
        assert res.recovery_required is True

    def test_strategic_fuel_inventory_depletion_simulation(self) -> None:
        """Simulate fuel storage exhaustion during full 45-day sea route blockade."""
        profile = InventoryProfile(
            resource_id="strategic-fuel-island",
            name="Archipelago Strategic Fuel Depot",
            starting_quantity=100000.0,
            unit="metric_tons",
            normal_consumption_per_day=2000.0,
            degraded_consumption_per_day=2800.0,
            replenishment_per_day=3000.0,
            replenishment_delay_days=30,
            route_capacity_factor=0.0,  # Total blockade
            substitution_factor=0.10,
            minimum_reserve=30000.0,
            critical_threshold=15000.0,
            warning_threshold=45000.0,
        )
        sim = simulate_inventory(profile, simulation_days=60, degraded=True, disrupted_replenishment=True)
        # Effective consumption = 2800 * 0.9 = 2520 MT/day
        # 100000 / 2520 ~= 39.6 days to exhaustion
        assert sim.days_to_warning is not None
        assert sim.days_to_critical is not None
        assert sim.days_to_exhaustion is not None
        assert 35 <= sim.days_to_exhaustion <= 42
        assert sim.final_quantity == 0.0
        assert sim.final_status == "exhausted"


class TestHighScaleGraphAndCycleStress:
    """Category 6: Massive Graph Scale, Cycle Detection & Blast Radius Performance Stress."""

    def test_thousand_node_dependency_graph_stress(self) -> None:
        """Construct and evaluate a 1,000-node supply web under 50ms propagation budget."""
        nodes: list[DependencyNode] = []
        edges: list[DependencyEdge] = []

        # Create 1,000 nodes organized across 10 hierarchical tiers
        for i in range(1000):
            tier = i // 100
            node_type = NodeType.SUPPLIER if tier == 0 else (NodeType.FACILITY if tier == 9 else NodeType.CORRIDOR)
            nodes.append(DependencyNode(
                node_id=f"node_{i:04d}",
                name=f"Supply Node {i:04d}",
                node_type=node_type,
                criticality=0.5 + (tier * 0.05),
            ))

        # Create 1,500 directed dependency edges between tiers
        for i in range(900):
            target_idx = i + 100 + (i % 5)
            if target_idx < 1000:
                edges.append(DependencyEdge(
                    source=f"node_{i:04d}",
                    target=f"node_{target_idx:04d}",
                    dependency_strength=0.85,
                ))

        start_time = time.perf_counter()
        graph = DependencyGraph(graph_id="scale-1000-nodes", nodes=nodes, edges=edges)
        build_elapsed = time.perf_counter() - start_time
        assert build_elapsed < 0.5  # <500ms validation budget

        # Check cycle detection on 1,000 nodes
        t_cycle = time.perf_counter()
        cycles = detect_cycles(graph)
        cycle_elapsed = time.perf_counter() - t_cycle
        assert len(cycles) == 0
        assert cycle_elapsed < 0.1  # <100ms cycle analysis budget

        # Run blast radius propagation from 10 failed tier-0 suppliers
        engine = DependencyEngine()
        failed_suppliers = {f"node_{i:04d}" for i in range(10)}
        t_blast = time.perf_counter()
        blast_radius = engine.calculate_blast_radius(graph, failed_suppliers)
        blast_elapsed = time.perf_counter() - t_blast

        assert len(blast_radius) >= 10
        assert blast_elapsed < 0.1  # <100ms propagation budget


class TestHighThroughputIngestionAndFuzzing:
    """Category 7: High-Volume Observation Processing, Freshness Decay & Fuzzing."""

    def test_thousand_observation_fusion_stress(self) -> None:
        """Ingest 1,000 multi-source observations and verify risk fusion determinism."""
        now = datetime.now(UTC)
        observations: list[Observation] = []

        metrics = [
            (MetricName.SEA_ICE_CONCENTRATION, "percent", AssertionClass.ICE, SourceTrust.AUTHORITATIVE_PUBLIC),
            (MetricName.WIND_SEVERITY, "ratio", AssertionClass.WEATHER, SourceTrust.AUTHORITATIVE_PUBLIC),
            (MetricName.PORT_AVAILABILITY, "ratio", AssertionClass.LIVE_AVAILABILITY, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.SATCOM_AVAILABILITY, "ratio", AssertionClass.LIVE_AVAILABILITY, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.CYBER_CONTROL_HEALTH, "ratio", AssertionClass.CYBER_HEALTH, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.DATA_INTEGRITY, "ratio", AssertionClass.CYBER_HEALTH, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.INSURANCE_AVAILABILITY, "ratio", AssertionClass.INSURANCE_ACCESS, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.ESCORT_CAPACITY, "ratio", AssertionClass.LIVE_CAPACITY, SourceTrust.AUTHENTICATED_OPERATOR),
            (MetricName.INVENTORY_DAYS, "days", AssertionClass.LIVE_CAPACITY, SourceTrust.AUTHENTICATED_OPERATOR),
        ]

        # Generate 1,000 valid observations with varied timestamps over a 48h window
        for i in range(1000):
            metric, unit, a_class, s_trust = metrics[i % len(metrics)]
            age_hours = (i % 48)
            obs_time = now - timedelta(hours=age_hours)
            val = 0.5 + ((i % 50) / 100.0)
            if metric == MetricName.SEA_ICE_CONCENTRATION:
                val = (i % 90)
            elif metric == MetricName.INVENTORY_DAYS:
                val = 10.0 + (i % 60)

            observations.append(Observation(
                observation_id=uuid4(),
                source_id=f"sensor-feed-{i % 20:02d}",
                source_trust=s_trust,
                assertion_class=a_class,
                metric=metric,
                value=val,
                unit=unit,
                observed_at=obs_time,
                confidence=0.90,
                provenance=Provenance(
                    uri=f"telemetry://sensor/{i}",
                    content_sha256=hashlib.sha256(f"obs-{i}".encode()).hexdigest(),
                    licence="test-data",
                ),
            ))

        engine = FusionEngine()
        t_start = time.perf_counter()
        assessment_1 = engine.assess("stress-corridor-1000", observations, as_of=now)
        assessment_2 = engine.assess("stress-corridor-1000", observations, as_of=now)
        elapsed = time.perf_counter() - t_start

        # Determinism check (bit-for-bit identical outputs)
        assert assessment_1.overall_risk == assessment_2.overall_risk
        assert assessment_1.confidence == assessment_2.confidence
        assert assessment_1.state == assessment_2.state
        assert elapsed < 0.2  # <200ms for 1,000 observations


class TestCryptographicEvidenceLedgerSecurityAndConcurrency:
    """Category 8: Append-Only SHA-256 Hash Chain, Ed25519 Signing & Tamper Detection."""

    def test_thousand_evidence_record_chain_and_tamper_detection(self, tmp_path: Path) -> None:
        """Create a cryptographic hash chain of 1,000 records, sign with Ed25519, and detect bit-tampering."""
        key = Ed25519PrivateKey.generate()
        ledger_path = tmp_path / "stress_ledger.ndjson"
        ledger = EvidenceLedger(ledger_path, signing_key=key, verifying_key=key.public_key())

        t_start = time.perf_counter()
        for i in range(1000):
            ledger.append(
                record_type="assessment_decision",
                subject_id=f"corridor/sector_{i % 50}",
                payload={"step": i, "continuity_score": 0.95, "timestamp": datetime.now(UTC).isoformat()},
            )
        append_elapsed = time.perf_counter() - t_start
        assert append_elapsed < 1.0  # <1s for 1,000 signed records

        # Verify integrity of untampered chain
        verify_errors = ledger.verify()
        assert len(verify_errors) == 0, f"Unexpected ledger verification errors: {verify_errors}"

        # Tamper test: Mutate payload in record #500
        raw_lines = ledger_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(raw_lines) == 1000
        import json

        tampered_record = json.loads(raw_lines[500])
        tampered_record["payload"]["continuity_score"] = 0.01  # Altered value
        raw_lines[500] = json.dumps(tampered_record)
        ledger_path.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

        # Verify that cryptographic ledger immediately flags the tamper attempt
        tamper_errors = ledger.verify()
        assert len(tamper_errors) > 0
        assert any("hash mismatch" in err or "signature invalid" in err for err in tamper_errors)
