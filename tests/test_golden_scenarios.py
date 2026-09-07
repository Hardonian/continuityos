"""Golden V1.0 Scenarios Test Suite (Scenarios A through J).

Covers canonical resilience edge cases specified in Section 26:
A. Commercial LEO loss -> Non-commercial fallback keeps network compliant
B. False communications redundancy -> Provider independence analyzer detects shared dependency
C. Physically open route / no insurance -> effectiveState = OPEN_BUT_UNINSURABLE
D. Correlated corridor failure -> Multiple corridor outage cascades, alternate route insufficient
E. Strategic inventory depletion -> Warning, critical, exhaustion, and assured replenishment timeline
F. Nominal reopening -> Reopened route remains degraded until backlog clears and reserves restore (T0-T5)
G. Conflicting evidence -> Conflicting reports across observation sources surfaced with discrepancy trace
H. Successful route substitution -> Alternative configuration passes all feasibility constraints
I. Failed route substitution -> Geographic alternative rejected due to port/rail capacity deficit
J. Provider concentration -> Declared redundancy downgraded due to upstream supplier/parent overlap
"""

from datetime import UTC, datetime
from pathlib import Path

from continuityos.closure import ClosureInput, assess_closure
from continuityos.domain import (
    CorridorState,
    PhysicalStateEnum,
)
from continuityos.evidence import EvidenceLedger
from continuityos.graph import DependencyEdge, DependencyGraph, DependencyNode, NodeType
from continuityos.independence import ProviderIndependenceAnalyzer
from continuityos.inventory import InventoryProfile, simulate_inventory
from continuityos.policy import (
    ContinuityPolicy,
    ObservedState,
    PolicyAssertion,
    PolicyRule,
    evaluate_policy,
)
from continuityos.recovery import RecoveryProfile, model_recovery
from continuityos.scenario import Scenario, ScenarioEvent, simulate_scenario
from continuityos.substitution import (
    RouteSubstitutionCandidate,
    compile_route_substitution,
)


class TestGoldenScenariosV1:
    """Golden Scenarios A through J validation suite."""

    def test_scenario_a_commercial_leo_loss_fallback_compliant(self) -> None:
        """Scenario A: Commercial LEO loss.

        When primary commercial LEO fails, protected government SATCOM and
        terrestrial fallback ensure communications redundancy meets policy.
        """
        policy = ContinuityPolicy(
            policy_id="comms-resilience-pol",
            version="1.0",
            rules=[
                PolicyRule(
                    rule_id="COMM-MIN-PROVIDERS",
                    description="Require at least 2 active comms channels",
                    assertion=PolicyAssertion(minimum_providers=2),
                ),
            ],
        )

        # Before failure: Commercial LEO + Govt SATCOM + HF Fallback = 3
        nominal_state = ObservedState(provider_counts={"comms": 3})
        nominal_res = evaluate_policy(policy, nominal_state)
        assert nominal_res.compliant is True

        # Scenario event: Commercial LEO constellation suffers severe geomagnetic disruption (1 lost -> 2 remaining)
        disrupted_state = ObservedState(provider_counts={"comms": 2})
        disrupted_res = evaluate_policy(policy, disrupted_state)
        # Even with commercial LEO lost, fallback keeps policy compliant (2 remaining)
        assert disrupted_res.compliant is True
        assert len(disrupted_res.violations) == 0

        # Complete loss of non-commercial fallbacks causes failure (< 2)
        failed_state = ObservedState(provider_counts={"comms": 1})
        failed_res = evaluate_policy(policy, failed_state)
        assert failed_res.compliant is False
        assert len(failed_res.violations) == 1

    def test_scenario_b_false_communications_redundancy_detected(self) -> None:
        """Scenario B: False communications redundancy.

        Provider independence analyzer identifies that two declared SATCOM
        providers share the same terrestrial teleport gateway, invalidating redundancy.
        """
        g = DependencyGraph(
            graph_id="graph-comms-check",
            nodes=[
                DependencyNode(
                    node_id="gateway/svalbard-station-01",
                    name="Svalbard Satellite Earth Station",
                    node_type=NodeType.FACILITY,
                ),
                DependencyNode(
                    node_id="provider/satcom-alpha",
                    name="LEO Broadband Alpha",
                    node_type=NodeType.SATCOM,
                ),
                DependencyNode(
                    node_id="provider/satcom-bravo",
                    name="GEO Constellation Bravo",
                    node_type=NodeType.SATCOM,
                ),
            ],
            edges=[
                DependencyEdge(
                    source="gateway/svalbard-station-01", target="provider/satcom-alpha"
                ),
                DependencyEdge(
                    source="gateway/svalbard-station-01", target="provider/satcom-bravo"
                ),
            ],
        )

        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(
            g,
            category="communications",
            provider_node_ids=["provider/satcom-alpha", "provider/satcom-bravo"],
            minimum_required=2,
        )

        assert res.declared_count == 2
        # Both share the upstream gateway chokepoint, so effective independent count is 1
        assert res.independent_count == 1
        assert res.redundancy_valid is False
        assert len(res.shared_dependencies) >= 1
        assert res.shared_dependencies[0].dependency_id == "gateway/svalbard-station-01"
        assert "REDUNDANCY INVALID" in res.format_text()

    def test_scenario_c_physically_open_route_no_insurance_closure(self) -> None:
        """Scenario C: Physically open route / no insurance.

        Physical access is unhindered (waterway clear), but war-risk underwriters
        withdraw coverage -> effective state is OPEN_BUT_UNINSURABLE.
        """
        closure_inp = ClosureInput(
            resource_ref="corridor/bab-el-mandeb",
            physically_accessible=True,
            physical_capacity_ratio=1.0,
            navigation_available=True,
            navigation_trust=0.95,
            communications_available=True,
            communications_trust=0.95,
            weather_safe=True,
            insurance_available=False,  # Underwriters withdrawn
            insurance_coverage=0.0,
            carrier_capacity_available=True,
            carrier_capacity_ratio=0.8,
        )
        assessment = assess_closure(closure_inp)

        assert assessment.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
        assert "uninsurable" in assessment.reason_codes
        composite = assessment.to_composite_state()
        assert composite.physical_state == PhysicalStateEnum.OPEN
        assert composite.commercial_state.insurance == "uninsurable"
        assert composite.effective_state == CorridorState.OPEN_BUT_UNINSURABLE

        # Human explain trace contains the commercial layer reasoning
        trace = assessment.explain()
        assert "OPEN_BUT_UNINSURABLE" in trace
        assert "uninsurable" in trace

    def test_scenario_d_correlated_corridor_failure(self) -> None:
        """Scenario D: Correlated corridor failure.

        Multi-corridor disruption (Hormuz + Bab-el-Mandeb + Malacca bottleneck)
        cascades through supply network, rendering alternate routes insufficient.
        """
        g = DependencyGraph(
            graph_id="graph-corridor-cascade",
            nodes=[
                DependencyNode(
                    node_id="supplier/gulf-crude",
                    name="Gulf Crude Terminal",
                    node_type=NodeType.SUPPLIER,
                ),
                DependencyNode(
                    node_id="corridor/hormuz", name="Strait of Hormuz", node_type=NodeType.CORRIDOR
                ),
                DependencyNode(
                    node_id="corridor/red-sea",
                    name="Red Sea Bab-el-Mandeb",
                    node_type=NodeType.CORRIDOR,
                ),
                DependencyNode(
                    node_id="route/suez", name="Suez Route", node_type=NodeType.CORRIDOR
                ),
                DependencyNode(
                    node_id="route/cape-good-hope",
                    name="Cape of Good Hope",
                    node_type=NodeType.CORRIDOR,
                ),
                DependencyNode(
                    node_id="dest/energy-terminal",
                    name="European Energy Terminal",
                    node_type=NodeType.FACILITY,
                ),
            ],
            edges=[
                DependencyEdge(source="supplier/gulf-crude", target="corridor/hormuz"),
                DependencyEdge(source="corridor/hormuz", target="route/suez"),
                DependencyEdge(source="route/suez", target="corridor/red-sea"),
                DependencyEdge(source="corridor/red-sea", target="dest/energy-terminal"),
                DependencyEdge(source="supplier/gulf-crude", target="route/cape-good-hope"),
                DependencyEdge(source="route/cape-good-hope", target="dest/energy-terminal"),
            ],
        )

        # Correlated disruption event targeting both primary corridors
        scenario = Scenario(
            scenario_id="scen-dual-chokepoint",
            name="dual-chokepoint-closure",
            events=[
                ScenarioEvent(
                    target="corridor/hormuz",
                    state=CorridorState.PHYSICALLY_CLOSED,
                ),
                ScenarioEvent(
                    target="corridor/red-sea",
                    state=CorridorState.FUNCTIONALLY_CLOSED,
                ),
            ],
        )

        res = simulate_scenario(scenario, g)
        assert len(res.failed_nodes) >= 2
        assert "corridor/hormuz" in res.failed_nodes
        assert "corridor/red-sea" in res.failed_nodes
        assert res.recovery_required is True

    def test_scenario_e_strategic_inventory_depletion_and_kpi(self) -> None:
        """Scenario E: Strategic inventory depletion.

        Calculates warning, critical, exhaustion dates, and verified
        assured_replenishment_days KPI under degraded burn rates.
        """
        profile = InventoryProfile(
            resource_id="inventory/arctic-diesel-reserve",
            name="Arctic Diesel Reserve",
            starting_quantity=12000.0,
            minimum_reserve=6000.0,
            warning_threshold=6000.0,
            critical_threshold=3000.0,
            normal_consumption_per_day=300.0,
            degraded_consumption_per_day=250.0,
            emergency_consumption_per_day=200.0,
            replenishment_per_day=600.0,
            replenishment_delay_days=30,
            shipment_delay_days=25,  # 30 + 25 = 55 days
        )

        res = simulate_inventory(profile, simulation_days=80, degraded=True)

        assert res.days_to_warning == 23
        assert res.days_to_critical == 35
        assert res.days_to_exhaustion == 47
        assert res.assured_replenishment_days == 55
        assert res.minimum_inventory_during_event == 0.0

        # Now test with timely replenishment arriving at Day 20
        profile_timely = InventoryProfile(
            resource_id="inventory/arctic-diesel-reserve",
            name="Arctic Diesel Reserve",
            starting_quantity=12000.0,
            minimum_reserve=6000.0,
            warning_threshold=6000.0,
            critical_threshold=3000.0,
            normal_consumption_per_day=300.0,
            degraded_consumption_per_day=250.0,
            emergency_consumption_per_day=200.0,
            replenishment_per_day=500.0,
            replenishment_delay_days=10,
            shipment_delay_days=10,  # 10 + 10 = 20 days
        )
        res_timely = simulate_inventory(profile_timely, simulation_days=50, degraded=True)
        assert res_timely.assured_replenishment_days == 20
        assert res_timely.days_to_exhaustion is None
        assert res_timely.minimum_inventory_during_event >= 7000.0

    def test_scenario_f_nominal_reopening_recovery_lag(self) -> None:
        """Scenario F: Nominal reopening.

        When physical access is restored at T1, the corridor is NOT healthy;
        carrier return, port backlogs, and inventory replenish take until T5.
        """
        profile = RecoveryProfile(
            resource_ref="corridor/suez-maritime",
            incident_description="Maritime grounding and canal obstruction",
            physical_reopening_days=5,
            port_backlog_days=18,
            vessel_repositioning_days=25,
            insurance_normalization_days=30,
            carrier_return_days=21,
            inventory_replenishment_days=45,
        )
        timeline_day6 = model_recovery(profile, days_since_incident=6)
        assert timeline_day6.reopened_but_not_healthy is True
        assert timeline_day6.is_healthy is False

        timeline_recovered = model_recovery(
            profile, days_since_incident=timeline_day6.total_recovery_days + 1
        )
        assert timeline_recovered.reopened_but_not_healthy is False
        assert timeline_recovered.is_healthy is True

    def test_scenario_g_conflicting_evidence_surfaced(self, tmp_path: Path) -> None:
        """Scenario G: Conflicting evidence.

        Conflicting reports between two observation sources (e.g., commercial AIS
        reporting route normal while SAR satellite detects blocked ice floe)
        are preserved in ledger and identified via find_conflicts.
        """
        ledger = EvidenceLedger(tmp_path / "ledger_conflicts.jsonl")

        now = datetime.now(UTC)
        # Commercial terrestrial AIS claims passage state is OPEN
        ledger.append(
            record_type="observation",
            subject_id="corridor/vilkitsky-strait",
            payload={
                "source_id": "terrestrial-ais-nordic",
                "state": "OPEN",
                "confidence": 0.65,
                "observed_at": now.isoformat(),
            },
        )
        # Military SAR radar detects severe multi-year pressure ridge blockages -> BLOCKED
        ledger.append(
            record_type="observation",
            subject_id="corridor/vilkitsky-strait",
            payload={
                "source_id": "sentinel-1-sar-radar",
                "state": "BLOCKED",
                "confidence": 0.98,
                "observed_at": now.isoformat(),
            },
        )

        conflicts = ledger.find_conflicts()
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert conflict["subject_id"] == "corridor/vilkitsky-strait"
        assert conflict["conflict_type"] == "state_conflict"
        assert "OPEN" in conflict["conflicting_states"]
        assert "BLOCKED" in conflict["conflicting_states"]

    def test_scenario_h_successful_route_substitution(self) -> None:
        """Scenario H: Successful route substitution.

        Alternative maritime corridor (North Atlantic + Rail) satisfies all
        geographical, ice class, port handling, rail, and inventory deadlines.
        """
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-arctic-atlantic",
            primary_route_id="Northern Sea Route (NSR)",
            alternative_route_id="North Atlantic Trans-Shipping Corridor via Kirkenes",
            cargo_type="bulk_fuel_and_spares",
            quantity_tons=10000.0,
            critical_inventory_exhaustion_days=45,
            alternative_transit_days=18,
            inland_rail_days=5,  # 18 + 5 = 23 days < 45 days
            port_handling_capacity_tons_day=8000.0,
            inland_rail_capacity_ratio=1.0,
            vessel_ice_class=True,
            route_requires_ice_class=True,
            carrier_available=True,
            insurance_available=True,
        )

        evaluation = compile_route_substitution(candidate)
        assert evaluation.geographically_viable is True
        assert evaluation.commercially_viable is True
        assert evaluation.arrival_before_critical_inventory_date is True
        assert evaluation.effective_substitution == "PASS"

        # Human report formatting confirms approval
        report = evaluation.format_report()
        assert "Effective substitution:                 PASS" in report

    def test_scenario_i_failed_route_substitution_capacity_deficit(self) -> None:
        """Scenario I: Failed route substitution.

        Pacific Rim alternative is geographically navigable and commercially insured,
        but rejected due to rail deficit and missing inventory arrival deadline.
        """
        candidate_fail = RouteSubstitutionCandidate(
            substitution_id="sub-arctic-pacific",
            primary_route_id="Northern Sea Route (NSR)",
            alternative_route_id="Pacific Overland Trans-Siberian Corridor",
            cargo_type="critical_chemicals",
            quantity_tons=10000.0,
            critical_inventory_exhaustion_days=25,
            alternative_transit_days=22,
            inland_rail_days=10,  # 22 + 10 = 32 days > 25 days deadline: DEADLINE MISSED
            port_handling_capacity_tons_day=0.0,  # 0.0 triggers port capacity FAIL
            inland_rail_capacity_ratio=0.15,  # <= 0.2 causes FAIL
            vessel_ice_class=False,
            route_requires_ice_class=False,
            carrier_available=True,
            insurance_available=True,
        )

        evaluation = compile_route_substitution(candidate_fail)
        assert evaluation.port_handling_capacity == "FAIL"
        assert evaluation.inland_rail_capacity == "FAIL"
        assert evaluation.arrival_before_critical_inventory_date is False
        assert evaluation.effective_substitution == "FAIL"

        report = evaluation.format_report()
        assert "Port handling capacity:                 FAIL" in report
        assert "Inland rail capacity:                   FAIL" in report
        assert "Arrival before critical inventory date: NO" in report
        assert "Effective substitution:                 FAIL" in report

    def test_scenario_j_provider_concentration_downgrades_redundancy(self) -> None:
        """Scenario J: Provider concentration.

        Three maritime fuel suppliers all source from the same upstream regional
        refinery monopoly, downgrading apparent supplier diversity from 3 to 1.
        """
        g = DependencyGraph(
            graph_id="graph-bunkering-check",
            nodes=[
                DependencyNode(
                    node_id="refinery/tromso-regional-refinery",
                    name="Tromso Regional Refinery",
                    node_type=NodeType.FACILITY,
                ),
                DependencyNode(
                    node_id="supplier/nordic-marine-fuel",
                    name="Nordic Marine Fuel AS",
                    node_type=NodeType.SUPPLIER,
                ),
                DependencyNode(
                    node_id="supplier/polar-bunker-express",
                    name="Polar Bunker Express",
                    node_type=NodeType.SUPPLIER,
                ),
                DependencyNode(
                    node_id="supplier/arctic-logistics-bunkering",
                    name="Arctic Logistics Bunkering",
                    node_type=NodeType.SUPPLIER,
                ),
            ],
            edges=[
                DependencyEdge(
                    source="refinery/tromso-regional-refinery", target="supplier/nordic-marine-fuel"
                ),
                DependencyEdge(
                    source="refinery/tromso-regional-refinery",
                    target="supplier/polar-bunker-express",
                ),
                DependencyEdge(
                    source="refinery/tromso-regional-refinery",
                    target="supplier/arctic-logistics-bunkering",
                ),
            ],
        )

        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(
            g,
            category="bunkering_fuel",
            provider_node_ids=[
                "supplier/nordic-marine-fuel",
                "supplier/polar-bunker-express",
                "supplier/arctic-logistics-bunkering",
            ],
            minimum_required=2,
        )

        assert res.declared_count == 3
        # Concentration reduces effective independent providers to 1
        assert res.independent_count == 1
        assert res.redundancy_valid is False
        assert len(res.shared_dependencies) >= 1
        assert res.shared_dependencies[0].dependency_id == "refinery/tromso-regional-refinery"
        assert "REDUNDANCY INVALID" in res.format_text()
