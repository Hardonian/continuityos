"""Tests for Kubernetes/Terraform-style reconciliation engine."""

from __future__ import annotations

from continuityos.reconcile import (
    ActualState,
    DesiredState,
    ReconciliationStatus,
    reconcile,
)


class TestReconciliation:
    def test_full_compliance(self) -> None:
        desired = DesiredState(
            satcom_provider_count=2,
            fuel_reserve_days=30.0,
            medical_reserve_days=45.0,
            minimum_routes=2,
            minimum_continuity=0.95,
        )
        actual = ActualState(
            satcom_provider_count=2,
            fuel_reserve_days=35.0,
            medical_reserve_days=60.0,
            route_count=3,
            overall_continuity=0.98,
        )
        res = reconcile(desired, actual)
        assert res.overall_status == ReconciliationStatus.COMPLIANT
        assert res.compliant_count == 5
        assert res.drift_count == 0
        assert res.fail_count == 0

    def test_drift_and_degraded_and_fail(self) -> None:
        desired = DesiredState(
            satcom_provider_count=3,  # actual 2 -> 2/3 = 66% (degraded)
            fuel_reserve_days=100.0,  # actual 85 -> 85/100 = 85% (drift)
            medical_reserve_days=50.0,  # actual 10 -> 10/50 = 20% (fail)
        )
        actual = ActualState(
            satcom_provider_count=2,
            fuel_reserve_days=85.0,
            medical_reserve_days=10.0,
        )
        res = reconcile(desired, actual)
        assert res.overall_status == ReconciliationStatus.FAIL
        assert res.fail_count == 1
        assert res.degraded_count == 1
        assert res.drift_count == 1

    def test_unknown_state_when_unobserved(self) -> None:
        desired = DesiredState(
            satcom_provider_count=2,
            fuel_reserve_days=30.0,
        )
        actual = ActualState(
            satcom_provider_count=2,
            fuel_reserve_days=None,  # Not observed
        )
        res = reconcile(desired, actual)
        assert res.unknown_count == 1
        assert res.overall_status == ReconciliationStatus.UNKNOWN
