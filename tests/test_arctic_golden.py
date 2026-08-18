"""Arctic Golden Reference Scenarios End-to-End Tests.

Validates the full Arctic reference implementation pipeline across all Golden
Scenarios A through G:
  Scenario A: Baseline Arctic transit
  Scenario B: Satcom outage + GNSS spoofing
  Scenario C: Port congestion + icebreaker propulsion loss
  Scenario D: Insurance loss (open_but_uninsurable)
  Scenario E: Correlated multi-system cyber-physical disruption
  Scenario F: Strategic fuel inventory depletion
  Scenario G: T0-T5 recovery lag timeline modeling
"""

from __future__ import annotations

from pathlib import Path

import yaml

from continuityos.closure import ClosureInput, assess_closure
from continuityos.domain import CorridorState
from continuityos.dsl import load_resource, validate_resource
from continuityos.graph import DependencyEngine, DependencyGraph, detect_cycles
from continuityos.inventory import InventoryProfile, simulate_inventory
from continuityos.policy import ContinuityPolicy, ObservedState, evaluate_policy
from continuityos.reconcile import ActualState, DesiredState, ReconciliationStatus, reconcile
from continuityos.recovery import RecoveryPhase, RecoveryProfile, model_recovery
from continuityos.remediation import generate_remediation
from continuityos.scenario import Scenario, simulate_scenario
from continuityos.trust import DependencyTrust, evaluate_trust


class TestArcticGoldenScenarios:
    def test_arctic_specs_validity(self) -> None:
        """Validate all Arctic YAML specs against JSON Schema DSL rules."""
        specs = [
            Path("examples/arctic/network.yaml"),
            Path("examples/arctic/policy.yaml"),
            Path("examples/arctic/trust/satcom.yaml"),
            Path("examples/arctic/trust/navigation.yaml"),
            Path("examples/arctic/scenarios/scenario_a_baseline.yaml"),
            Path("examples/arctic/scenarios/scenario_b_satcom_nav_loss.yaml"),
            Path("examples/arctic/scenarios/scenario_c_port_icebreaker.yaml"),
            Path("examples/arctic/scenarios/scenario_d_insurance_loss.yaml"),
            Path("examples/arctic/scenarios/scenario_e_correlated_multisystem.yaml"),
        ]
        for spec_path in specs:
            resource = load_resource(spec_path)
            errors = validate_resource(resource)
            assert errors == [], f"Validation errors in {spec_path}: {errors}"

    def test_arctic_graph_acyclic(self) -> None:
        """Arctic graph has no circular dependencies."""
        raw = yaml.safe_load(Path("examples/arctic/graph.yaml").read_text(encoding="utf-8"))
        graph = DependencyGraph.model_validate(raw)
        cycles = detect_cycles(graph)
        assert len(cycles) == 0

    def test_scenario_a_baseline(self) -> None:
        """Scenario A: Baseline conditions maintain full continuity."""
        raw_graph = yaml.safe_load(Path("examples/arctic/graph.yaml").read_text(encoding="utf-8"))
        graph = DependencyGraph.model_validate(raw_graph)
        raw_scen = yaml.safe_load(Path("examples/arctic/scenarios/scenario_a_baseline.yaml").read_text(encoding="utf-8"))
        scenario = Scenario(
            scenario_id="scenario-a",
            name="Baseline",
            events=raw_scen["spec"]["events"],
            duration_days=raw_scen["spec"]["duration_days"],
        )
        res = simulate_scenario(scenario, graph)
        assert res.events_applied == 0
        assert len(res.failed_nodes) == 0
        assert res.total_capacity_loss == 0.0
        assert res.recovery_required is False

    def test_scenario_b_satcom_nav_loss(self) -> None:
        """Scenario B: Satcom loss attenuates routes via substitute group."""
        raw_graph = yaml.safe_load(Path("examples/arctic/graph.yaml").read_text(encoding="utf-8"))
        graph = DependencyGraph.model_validate(raw_graph)
        raw_scen = yaml.safe_load(Path("examples/arctic/scenarios/scenario_b_satcom_nav_loss.yaml").read_text(encoding="utf-8"))
        scenario = Scenario(
            scenario_id="scenario-b",
            name="Satcom Nav Loss",
            events=raw_scen["spec"]["events"],
            duration_days=raw_scen["spec"]["duration_days"],
        )
        res = simulate_scenario(scenario, graph)
        assert "satcom_iridium" in res.failed_nodes
        assert res.recovery_required is True

    def test_scenario_c_port_icebreaker(self) -> None:
        """Scenario C: Port outage and icebreaker escort failure."""
        raw_graph = yaml.safe_load(Path("examples/arctic/graph.yaml").read_text(encoding="utf-8"))
        graph = DependencyGraph.model_validate(raw_graph)
        raw_scen = yaml.safe_load(Path("examples/arctic/scenarios/scenario_c_port_icebreaker.yaml").read_text(encoding="utf-8"))
        scenario = Scenario(
            scenario_id="scenario-c",
            name="Port Icebreaker Failure",
            events=raw_scen["spec"]["events"],
            duration_days=raw_scen["spec"]["duration_days"],
        )
        res = simulate_scenario(scenario, graph)
        assert len(res.failed_nodes) == 2
        assert "port_murmansk" in res.failed_nodes
        assert "icebreaker_50let" in res.failed_nodes
        assert res.total_capacity_loss > 0.3

    def test_scenario_d_insurance_loss_closure(self) -> None:
        """Scenario D: Insurance loss triggers OPEN_BUT_UNINSURABLE functional closure."""
        inp = ClosureInput(
            resource_ref="corridor/northern-sea-route",
            physically_accessible=True,
            navigation_available=True,
            communications_available=True,
            insurance_available=False,
            insurance_coverage=0.0,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
        assert "uninsurable" in assessment.reason_codes

    def test_scenario_e_correlated_multisystem(self) -> None:
        """Scenario E: Correlated failure cascade across all layers."""
        raw_graph = yaml.safe_load(Path("examples/arctic/graph.yaml").read_text(encoding="utf-8"))
        graph = DependencyGraph.model_validate(raw_graph)
        raw_scen = yaml.safe_load(Path("examples/arctic/scenarios/scenario_e_correlated_multisystem.yaml").read_text(encoding="utf-8"))
        scenario = Scenario(
            scenario_id="scenario-e",
            name="Correlated Multi-System",
            events=raw_scen["spec"]["events"],
            duration_days=raw_scen["spec"]["duration_days"],
        )
        res = simulate_scenario(scenario, graph)
        assert len(res.failed_nodes) == 3
        assert res.total_capacity_loss > 0.4
        assert res.recovery_required is True

    def test_scenario_f_fuel_depletion(self) -> None:
        """Scenario F: Fuel inventory depletion with replenishment delay."""
        raw_f = yaml.safe_load(Path("examples/arctic/scenarios/scenario_f_fuel_depletion.yaml").read_text(encoding="utf-8"))
        profile = InventoryProfile.model_validate(raw_f)
        res = simulate_inventory(profile, simulation_days=60, degraded=True)
        assert res.starting_quantity == 50000.0
        assert res.days_to_warning is not None
        assert len(res.daily_log) == 60

    def test_scenario_g_recovery_lag(self) -> None:
        """Scenario G: Recovery lag timeline modeling T0 through T5."""
        raw_g = yaml.safe_load(Path("examples/arctic/scenarios/scenario_g_recovery_lag.yaml").read_text(encoding="utf-8"))
        profile = RecoveryProfile.model_validate(raw_g)
        timeline = model_recovery(profile, days_since_incident=10)
        assert timeline.total_recovery_days > profile.physical_reopening_days
        assert timeline.current_phase == RecoveryPhase.T1_PHYSICAL_REOPENING
        assert len(timeline.milestones) == 6
        assert timeline.bottleneck is not None

    def test_end_to_end_reconciliation_and_remediation(self) -> None:
        """Full pipeline: policy -> observed state -> reconciliation -> advisory remediation."""
        raw_policy = yaml.safe_load(Path("examples/arctic/policy.yaml").read_text(encoding="utf-8"))
        policy = ContinuityPolicy(
            policy_id=raw_policy["metadata"]["name"],
            rules=raw_policy["spec"]["rules"],
        )
        # Disrupted state where SATCOM is single-provider and fuel is degraded
        state = ObservedState(
            provider_counts={"satcom": 1},
            reserve_days={"fuel": 25.0},
            independent_route_count=1,
            overall_continuity=0.78,
            trust_scores={"navigation": 0.55},
        )
        evaluation = evaluate_policy(policy, state)
        assert evaluation.compliant is False
        assert len(evaluation.violations) >= 3

        # Reconcile desired vs actual
        desired = DesiredState(
            satcom_provider_count=2,
            fuel_reserve_days=45.0,
            minimum_routes=2,
            minimum_continuity=0.95,
        )
        actual = ActualState(
            satcom_provider_count=1,
            fuel_reserve_days=25.0,
            route_count=1,
            overall_continuity=0.78,
        )
        recon_result = reconcile(desired, actual)
        assert recon_result.overall_status in {ReconciliationStatus.FAIL, ReconciliationStatus.DEGRADED}

        # Generate advisory remediation
        remediation_plan = generate_remediation(recon_result)
        assert len(remediation_plan.options) >= 3
        assert remediation_plan.total_estimated_improvement > 0.0
        assert "advisory" in remediation_plan.advisory_notice.lower()
