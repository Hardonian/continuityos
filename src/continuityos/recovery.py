"""Recovery lag engine.

Models the critical insight that route reopened ≠ system recovered.
After a disruption, recovery progresses through distinct phases from
physical reopening through full resilience restoration.

Recovery timeline:
    T0 — Incident occurs
    T1 — Physical reopening (route/port/facility reopened)
    T2 — Commercial normalization (insurance, carriers return)
    T3 — Logistics normalization (vessels repositioned, schedules resume)
    T4 — Inventory replenishment (reserves rebuilt)
    T5 — Full resilience restoration (all policies met)
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class RecoveryPhase(StrEnum):
    T0_INCIDENT = "T0_incident"
    T1_PHYSICAL_REOPENING = "T1_physical_reopening"
    T2_COMMERCIAL_NORMALIZATION = "T2_commercial_normalization"
    T3_LOGISTICS_NORMALIZATION = "T3_logistics_normalization"
    T4_INVENTORY_REPLENISHMENT = "T4_inventory_replenishment"
    T5_FULL_RESTORATION = "T5_full_restoration"


class RecoveryMilestone(BaseModel):
    """A single milestone in the recovery timeline."""

    phase: RecoveryPhase
    description: str
    estimated_days: int = Field(ge=0, le=3650)
    dependencies: list[str] = Field(default_factory=list)
    confidence: Score = 0.5


class RecoveryProfile(BaseModel):
    """Configuration for recovery lag modeling."""

    resource_ref: str = Field(min_length=1, max_length=256)
    incident_description: str = Field(min_length=1, max_length=512)

    # Phase durations
    physical_reopening_days: int = Field(default=0, ge=0, le=365)
    port_backlog_days: int = Field(default=7, ge=0, le=365)
    vessel_repositioning_days: int = Field(default=14, ge=0, le=365)
    carrier_return_days: int = Field(default=21, ge=0, le=365)
    insurance_normalization_days: int = Field(default=30, ge=0, le=365)
    inventory_replenishment_days: int = Field(default=45, ge=0, le=365)
    equipment_availability_days: int = Field(default=10, ge=0, le=365)
    warehouse_recovery_days: int = Field(default=14, ge=0, le=365)
    production_restart_days: int = Field(default=21, ge=0, le=365)


class RecoveryTimeline(BaseModel):
    """Complete recovery lag assessment."""

    timeline_id: UUID = Field(default_factory=uuid4)
    resource_ref: str
    incident_description: str
    milestones: list[RecoveryMilestone]
    total_recovery_days: int
    current_phase: RecoveryPhase
    recovery_progress: Score
    bottleneck: str | None
    summary: str


def model_recovery(
    profile: RecoveryProfile,
    *,
    days_since_incident: int = 0,
) -> RecoveryTimeline:
    """Model recovery lag for a disrupted resource.

    Returns a timeline with milestones showing that system recovery
    extends well beyond physical reopening.
    """
    milestones: list[RecoveryMilestone] = []

    # T0: Incident
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T0_INCIDENT,
        description=profile.incident_description,
        estimated_days=0,
        confidence=1.0,
    ))

    # T1: Physical reopening
    t1_days = profile.physical_reopening_days
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T1_PHYSICAL_REOPENING,
        description="Physical infrastructure reopened or restored",
        estimated_days=t1_days,
        dependencies=["physical_access", "safety_clearance"],
        confidence=0.8,
    ))

    # T2: Commercial normalization
    t2_days = t1_days + max(
        profile.insurance_normalization_days,
        profile.carrier_return_days,
    )
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T2_COMMERCIAL_NORMALIZATION,
        description="Insurance coverage restored, carriers return to service",
        estimated_days=t2_days,
        dependencies=["insurance_underwriting", "carrier_contracts", "market_confidence"],
        confidence=0.6,
    ))

    # T3: Logistics normalization
    t3_days = t2_days + max(
        profile.vessel_repositioning_days,
        profile.port_backlog_days,
        profile.equipment_availability_days,
    )
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T3_LOGISTICS_NORMALIZATION,
        description="Vessels repositioned, port backlog cleared, schedules resume",
        estimated_days=t3_days,
        dependencies=[
            "vessel_repositioning", "port_backlog_clearance",
            "schedule_normalization", "equipment_restoration",
        ],
        confidence=0.5,
    ))

    # T4: Inventory replenishment
    t4_days = t3_days + max(
        profile.inventory_replenishment_days,
        profile.warehouse_recovery_days,
        profile.production_restart_days,
    )
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T4_INVENTORY_REPLENISHMENT,
        description="Strategic reserves rebuilt to policy-required levels",
        estimated_days=t4_days,
        dependencies=["supply_flow", "warehouse_capacity", "production_capacity"],
        confidence=0.4,
    ))

    # T5: Full restoration
    t5_days = t4_days + 7  # Buffer for verification and confidence building
    milestones.append(RecoveryMilestone(
        phase=RecoveryPhase.T5_FULL_RESTORATION,
        description="All resilience policies met, full operational confidence restored",
        estimated_days=t5_days,
        dependencies=["policy_compliance", "operational_confidence"],
        confidence=0.35,
    ))

    total_days = t5_days

    # Determine current phase based on days since incident
    current = RecoveryPhase.T0_INCIDENT
    for ms in milestones:
        if days_since_incident >= ms.estimated_days:
            current = ms.phase

    # Calculate progress
    progress = min(1.0, days_since_incident / total_days) if total_days > 0 else 0.0

    # Find bottleneck (longest phase transition)
    phase_durations = [
        (RecoveryPhase.T1_PHYSICAL_REOPENING, t1_days),
        (RecoveryPhase.T2_COMMERCIAL_NORMALIZATION, t2_days - t1_days),
        (RecoveryPhase.T3_LOGISTICS_NORMALIZATION, t3_days - t2_days),
        (RecoveryPhase.T4_INVENTORY_REPLENISHMENT, t4_days - t3_days),
    ]
    bottleneck_phase, bottleneck_days = max(phase_durations, key=lambda x: x[1])
    bottleneck = f"{bottleneck_phase}: {bottleneck_days} days"

    summary_parts = [
        f"Incident: {profile.incident_description}",
        f"Physical reopening: day {t1_days}",
        f"Commercial normalization: day {t2_days}",
        f"Logistics normalization: day {t3_days}",
        f"Inventory replenishment: day {t4_days}",
        f"Full restoration: day {t5_days}",
        f"Bottleneck: {bottleneck}",
    ]
    if days_since_incident > 0:
        summary_parts.append(f"Current phase: {current} (day {days_since_incident})")

    return RecoveryTimeline(
        resource_ref=profile.resource_ref,
        incident_description=profile.incident_description,
        milestones=milestones,
        total_recovery_days=total_days,
        current_phase=current,
        recovery_progress=round(progress, 6),
        bottleneck=bottleneck,
        summary="; ".join(summary_parts),
    )
