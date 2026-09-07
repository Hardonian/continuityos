"""Unit and integration tests for Assurance Budgeting Engine."""

from uuid import UUID

import pytest

from continuityos.assurance import (
    AssuranceObservedState,
    evaluate_assurance,
)
from continuityos.dsl import (
    AssuranceCommercialSpec,
    AssuranceEvidenceSpec,
    AssuranceInventorySpec,
    AssuranceObjectiveSpec,
    AssurancePolicySpec,
    AssuranceRecoverySpec,
    AssuranceToleranceSpec,
)


class TestAssuranceBudgeting:
    """Tests for AssurancePolicySpec evaluation and scorecard reporting."""

    @pytest.fixture
    def nominal_policy(self) -> AssurancePolicySpec:
        return AssurancePolicySpec(
            continuity_objective=AssuranceObjectiveSpec(minimum=0.95),
            tolerate=AssuranceToleranceSpec(
                corridor_loss=1,
                port_loss=1,
                communication_provider_loss=1,
                navigation_source_loss=2,
                observation_source_loss=1,
            ),
            evidence=AssuranceEvidenceSpec(
                minimum_independent_operational_sources=2,
                minimum_independent_navigation_sources=3,
                minimum_independent_environmental_sources=2,
            ),
            commercial=AssuranceCommercialSpec(
                minimum_carrier_options=2,
                insurance_required=True,
            ),
            inventory=AssuranceInventorySpec(
                minimum_reserve_days=30,
                minimum_assured_replenishment_cycles=1,
            ),
            recovery=AssuranceRecoverySpec(
                verify_carrier_return=True,
                verify_backlog_clearance=True,
                verify_reserve_restoration=True,
            ),
        )

    @pytest.fixture
    def compliant_state(self) -> AssuranceObservedState:
        return AssuranceObservedState(
            continuity_score=0.97,
            available_corridors=2,
            available_ports=2,
            independent_comm_providers=2,
            independent_nav_sources=3,
            independent_obs_sources=2,
            independent_operational_sources=3,
            independent_environmental_sources=2,
            carrier_options=3,
            insurance_verified=True,
            reserve_days=45.0,
            assured_replenishment_cycles=2,
            carrier_return_verified=True,
            backlog_clearance_verified=True,
            reserve_restoration_verified=True,
        )

    def test_evaluate_assurance_fully_compliant(
        self, nominal_policy: AssurancePolicySpec, compliant_state: AssuranceObservedState
    ) -> None:
        scorecard = evaluate_assurance(
            nominal_policy, compliant_state, policy_name="test-compliant"
        )

        assert scorecard.overall_compliant is True
        assert scorecard.assurance_score == 1.0
        assert len(scorecard.failed_dimensions) == 0
        assert isinstance(scorecard.scorecard_id, UUID)
        assert len(scorecard.dimensions) >= 12

        table = scorecard.format_table()
        assert "COMPLIANT" in table
        assert "100.0%" in table
        assert "All declared assurance constraints satisfied." in table

    def test_evaluate_assurance_objective_deficit(
        self, nominal_policy: AssurancePolicySpec, compliant_state: AssuranceObservedState
    ) -> None:
        compliant_state.continuity_score = 0.88  # below 0.95 minimum
        scorecard = evaluate_assurance(nominal_policy, compliant_state, policy_name="test-obj-fail")

        assert scorecard.overall_compliant is False
        assert any("continuity_objective" in fd for fd in scorecard.failed_dimensions)
        table = scorecard.format_table()
        assert "NON-COMPLIANT" in table
        assert "OBJECTIVE" in table

    def test_evaluate_assurance_insurance_and_carrier_failure(
        self, nominal_policy: AssurancePolicySpec, compliant_state: AssuranceObservedState
    ) -> None:
        compliant_state.insurance_verified = False
        compliant_state.carrier_options = 1  # requires 2
        scorecard = evaluate_assurance(
            nominal_policy, compliant_state, policy_name="test-commercial-fail"
        )

        assert scorecard.overall_compliant is False
        assert any(
            "insurance_verified" in fd or "insurance" in fd for fd in scorecard.failed_dimensions
        )
        assert any("carrier_options" in fd for fd in scorecard.failed_dimensions)

    def test_evaluate_assurance_inventory_deficit(
        self, nominal_policy: AssurancePolicySpec, compliant_state: AssuranceObservedState
    ) -> None:
        compliant_state.reserve_days = 20.0  # requires 30
        compliant_state.assured_replenishment_cycles = 0  # requires 1
        scorecard = evaluate_assurance(nominal_policy, compliant_state, policy_name="test-inv-fail")

        assert scorecard.overall_compliant is False
        assert any("reserve_days" in fd for fd in scorecard.failed_dimensions)
        assert any("assured_replenishment_cycles" in fd for fd in scorecard.failed_dimensions)

    def test_evaluate_assurance_recovery_unverified(
        self, nominal_policy: AssurancePolicySpec, compliant_state: AssuranceObservedState
    ) -> None:
        compliant_state.backlog_clearance_verified = False
        compliant_state.reserve_restoration_verified = False
        scorecard = evaluate_assurance(nominal_policy, compliant_state, policy_name="test-rec-fail")

        assert scorecard.overall_compliant is False
        assert any(
            "backlog_clearance_verified" in fd or "backlog" in fd
            for fd in scorecard.failed_dimensions
        )
        assert any(
            "reserve_restoration_verified" in fd or "reserve" in fd
            for fd in scorecard.failed_dimensions
        )

    def test_empty_or_zero_values_fail_gracefully(
        self, nominal_policy: AssurancePolicySpec
    ) -> None:
        empty_state = AssuranceObservedState(
            continuity_score=0.0,
            available_corridors=0,
            available_ports=0,
            independent_comm_providers=0,
            carrier_options=0,
            insurance_verified=False,
            reserve_days=0.0,
            assured_replenishment_cycles=0,
            carrier_return_verified=False,
            backlog_clearance_verified=False,
            reserve_restoration_verified=False,
        )
        scorecard = evaluate_assurance(nominal_policy, empty_state, policy_name="test-empty")

        assert scorecard.overall_compliant is False
        assert len(scorecard.failed_dimensions) > 0
        table = scorecard.format_table()
        assert "Failed Dimensions" in table
