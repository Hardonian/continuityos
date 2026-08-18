"""Tests for Advisory Remediation engine."""

from __future__ import annotations

from continuityos.reconcile import (
    ActualState,
    DesiredState,
    reconcile,
)
from continuityos.remediation import (
    generate_remediation,
)


class TestRemediationEngine:
    def test_remediation_generated_for_violations(self) -> None:
        desired = DesiredState(
            satcom_provider_count=2,
            fuel_reserve_days=30.0,
            minimum_routes=2,
        )
        actual = ActualState(
            satcom_provider_count=1,  # Fails
            fuel_reserve_days=15.0,   # Fails
            route_count=1,            # Fails
        )
        recon_result = reconcile(desired, actual)
        remediation_plan = generate_remediation(recon_result)

        assert len(remediation_plan.options) > 0
        assert remediation_plan.total_estimated_improvement > 0.0
        assert "advisory" in remediation_plan.advisory_notice.lower()
        assert all(opt.requires_human_approval for opt in remediation_plan.options)

    def test_no_remediation_needed_when_compliant(self) -> None:
        desired = DesiredState(
            satcom_provider_count=2,
            fuel_reserve_days=30.0,
        )
        actual = ActualState(
            satcom_provider_count=2,
            fuel_reserve_days=35.0,
        )
        recon_result = reconcile(desired, actual)
        remediation_plan = generate_remediation(recon_result)
        assert len(remediation_plan.options) == 0
        assert remediation_plan.total_estimated_improvement == 0.0
