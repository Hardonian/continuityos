"""Tests for Recovery Lag timeline modeling engine."""

from __future__ import annotations

from continuityos.recovery import (
    RecoveryPhase,
    RecoveryProfile,
    model_recovery,
)


class TestRecoveryLag:
    def test_milestone_generation(self) -> None:
        profile = RecoveryProfile(
            resource_ref="route/nsr",
            incident_description="Sea ice blockage and port damage",
            physical_reopening_days=10,
            insurance_normalization_days=25,
            carrier_return_days=20,
            port_backlog_days=15,
            inventory_replenishment_days=30,
        )
        timeline = model_recovery(profile, days_since_incident=0)
        assert len(timeline.milestones) == 6
        assert timeline.milestones[0].phase == RecoveryPhase.T0_INCIDENT
        assert timeline.milestones[1].phase == RecoveryPhase.T1_PHYSICAL_REOPENING
        assert timeline.milestones[2].phase == RecoveryPhase.T2_COMMERCIAL_NORMALIZATION
        assert timeline.milestones[3].phase == RecoveryPhase.T3_LOGISTICS_NORMALIZATION
        assert timeline.milestones[4].phase == RecoveryPhase.T4_INVENTORY_REPLENISHMENT
        assert timeline.milestones[5].phase == RecoveryPhase.T5_FULL_RESTORATION

        # Total days should be strictly greater than physical reopening
        assert timeline.total_recovery_days > profile.physical_reopening_days
        assert timeline.bottleneck is not None

    def test_progress_tracking(self) -> None:
        profile = RecoveryProfile(
            resource_ref="port/murmansk",
            incident_description="Cranes damaged",
            physical_reopening_days=5,
            carrier_return_days=10,
            insurance_normalization_days=10,
        )
        timeline_day_0 = model_recovery(profile, days_since_incident=0)
        assert timeline_day_0.current_phase == RecoveryPhase.T0_INCIDENT
        assert timeline_day_0.recovery_progress == 0.0

        timeline_day_6 = model_recovery(profile, days_since_incident=6)
        assert timeline_day_6.current_phase == RecoveryPhase.T1_PHYSICAL_REOPENING
        assert timeline_day_6.recovery_progress > 0.0
