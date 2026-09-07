"""Functional closure engine.

Detects infrastructure that is technically available but functionally unusable.
This is the core insight of ContinuityOS: infrastructure can remain technically
open while becoming operationally or commercially unusable.

The engine decomposes state into four independent layers:
    physical  → is the infrastructure physically accessible?
    operational → can operations actually use it?
    commercial → is it commercially viable (insured, carriers, capacity)?
    trust → is the information/navigation/communications trustworthy?

The effective state is derived from the combination of all layers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import (
    CommercialState,
    CorridorState,
    DigitalTrustState,
    EffectiveCorridorState,
    OperationalState,
    PhysicalStateEnum,
    RecoveryState,
    RecoveryStateEnum,
    Score,
)


class LayerState(StrEnum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ClosureLayer(BaseModel):
    """State assessment for a single closure layer."""

    layer: str
    state: LayerState
    confidence: Score
    reason_codes: list[str]
    supporting_evidence: list[str] = Field(default_factory=list)


class ClosureAssessment(BaseModel):
    """Complete functional closure assessment."""

    assessment_id: UUID = Field(default_factory=uuid4)
    resource_ref: str
    physical_state: ClosureLayer
    operational_state: ClosureLayer
    commercial_state: ClosureLayer
    trust_state: ClosureLayer
    recovery_state: ClosureLayer = Field(
        default_factory=lambda: ClosureLayer(
            layer="recovery",
            state=LayerState.AVAILABLE,
            confidence=1.0,
            reason_codes=[],
        )
    )
    effective_state: CorridorState
    reason_codes: list[str]
    confidence: Score
    policy_violations: list[str] = Field(default_factory=list)
    dependency_trace: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_composite_state(self) -> EffectiveCorridorState:
        """Convert multi-layer assessment into canonical EffectiveCorridorState."""
        phys = (
            PhysicalStateEnum.PHYSICALLY_CLOSED
            if self.physical_state.state == LayerState.UNAVAILABLE
            else PhysicalStateEnum.CAPACITY_CONSTRAINED
            if self.physical_state.state == LayerState.DEGRADED
            else PhysicalStateEnum.OPEN
        )
        return EffectiveCorridorState(
            physical_state=phys,
            operational_state=OperationalState(
                navigation="degraded"
                if "navigation_untrusted" in self.operational_state.reason_codes
                else "unavailable"
                if "navigation_unavailable" in self.operational_state.reason_codes
                else "healthy",
                communications="degraded"
                if "communications_degraded" in self.operational_state.reason_codes
                else "unavailable"
                if "communications_unavailable" in self.operational_state.reason_codes
                else "healthy",
                escort_service="dependent"
                if "service_dependent" in self.operational_state.reason_codes
                else "available",
            ),
            commercial_state=CommercialState(
                carrier_capacity="unavailable"
                if "no_carrier_capacity" in self.commercial_state.reason_codes
                else "available",
                insurance="uninsurable"
                if "uninsurable" in self.commercial_state.reason_codes
                else "available",
                commercial_viability=self.commercial_state.confidence,
            ),
            digital_trust_state=DigitalTrustState(
                navigation_integrity=0.3
                if "navigation_untrusted" in self.operational_state.reason_codes
                else 1.0,
                communications_integrity=0.4
                if "communications_degraded" in self.operational_state.reason_codes
                else 1.0,
                cyber_integrity=self.trust_state.confidence,
                data_integrity=self.trust_state.confidence,
            ),
            recovery_state=RecoveryState(
                phase=RecoveryStateEnum.BACKLOG_ACTIVE
                if "recovery_backlogged" in self.recovery_state.reason_codes
                else RecoveryStateEnum.NORMAL,
                backlog_active="recovery_backlogged" in self.recovery_state.reason_codes,
            ),
            effective_state=self.effective_state,
            reason_codes=self.reason_codes,
        )

    def explain(self) -> str:
        """Generate human-readable functional closure trace."""
        lines = [
            "=" * 78,
            "CONTINUITYOS FUNCTIONAL CLOSURE EXPLANATION TRACE",
            "=" * 78,
            f"Resource:        {self.resource_ref}",
            f"Effective State: {self.effective_state.value.upper()}",
            f"Confidence:      {self.confidence:.1%}",
            f"Timestamp:       {self.timestamp.isoformat()}",
            "",
            "Four-Layer Decomposition + Recovery Status:",
            f"  [PHYSICAL]      {self.physical_state.state.value.upper():<12} (conf: {self.physical_state.confidence:.2f})"
            + (
                f" -> {', '.join(self.physical_state.reason_codes)}"
                if self.physical_state.reason_codes
                else ""
            ),
            f"  [OPERATIONAL]   {self.operational_state.state.value.upper():<12} (conf: {self.operational_state.confidence:.2f})"
            + (
                f" -> {', '.join(self.operational_state.reason_codes)}"
                if self.operational_state.reason_codes
                else ""
            ),
            f"  [COMMERCIAL]    {self.commercial_state.state.value.upper():<12} (conf: {self.commercial_state.confidence:.2f})"
            + (
                f" -> {', '.join(self.commercial_state.reason_codes)}"
                if self.commercial_state.reason_codes
                else ""
            ),
            f"  [DIGITAL TRUST] {self.trust_state.state.value.upper():<12} (conf: {self.trust_state.confidence:.2f})"
            + (
                f" -> {', '.join(self.trust_state.reason_codes)}"
                if self.trust_state.reason_codes
                else ""
            ),
            f"  [RECOVERY]      {self.recovery_state.state.value.upper():<12} (conf: {self.recovery_state.confidence:.2f})"
            + (
                f" -> {', '.join(self.recovery_state.reason_codes)}"
                if self.recovery_state.reason_codes
                else ""
            ),
            "",
            "Reason Codes:",
        ]
        if self.reason_codes:
            for rc in self.reason_codes:
                lines.append(f"  - {rc}")
        else:
            lines.append("  (none - nominal operational conditions)")

        if self.policy_violations:
            lines.append("")
            lines.append("Policy Violations:")
            for pv in self.policy_violations:
                lines.append(f"  ! {pv}")

        if self.dependency_trace:
            lines.append("")
            lines.append("Dependency Trace:")
            for dt in self.dependency_trace:
                lines.append(f"  -> {dt}")

        if self.evidence_refs or self.supporting_evidence:
            lines.append("")
            lines.append("Evidence References:")
            for ev in self.evidence_refs or self.supporting_evidence:
                lines.append(f"  * {ev}")

        lines.append("=" * 78)
        return "\n".join(lines)


class ClosureInput(BaseModel):
    """Input factors for functional closure assessment."""

    resource_ref: str = Field(min_length=1, max_length=256)

    # Physical layer
    physically_accessible: bool = True
    physical_capacity_ratio: Score = 1.0

    # Operational layer
    navigation_available: bool = True
    navigation_trust: Score = 1.0
    communications_available: bool = True
    communications_trust: Score = 1.0
    escort_available: bool = True
    escort_dependent: bool = False
    weather_safe: bool = True

    # Commercial layer
    insurance_available: bool = True
    insurance_coverage: Score = 1.0
    carrier_capacity_available: bool = True
    carrier_capacity_ratio: Score = 1.0
    commercial_viability: Score = 1.0

    # Trust layer
    data_integrity: Score = 1.0
    observation_confidence: Score = 1.0
    source_diversity: int = Field(default=2, ge=0)

    # Recovery layer
    recovery_backlog_active: bool = False

    # Optional metadata
    policy_violations: list[str] = Field(default_factory=list)
    dependency_trace: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


def assess_closure(inp: ClosureInput) -> ClosureAssessment:
    """Assess functional closure of a resource across physical, operational, commercial, trust, and recovery layers."""
    physical = _assess_physical(inp)
    operational = _assess_operational(inp)
    commercial = _assess_commercial(inp)
    trust = _assess_trust(inp)
    recovery = _assess_recovery(inp)

    effective_state = _derive_effective_state(physical, operational, commercial, trust, recovery)
    all_reasons = (
        physical.reason_codes
        + operational.reason_codes
        + commercial.reason_codes
        + trust.reason_codes
        + recovery.reason_codes
    )
    all_evidence = (
        physical.supporting_evidence
        + operational.supporting_evidence
        + commercial.supporting_evidence
        + trust.supporting_evidence
        + recovery.supporting_evidence
        + inp.evidence_refs
    )
    confidences = [
        physical.confidence,
        operational.confidence,
        commercial.confidence,
        trust.confidence,
        recovery.confidence,
    ]
    overall_confidence = min(confidences) if confidences else 0.0

    return ClosureAssessment(
        resource_ref=inp.resource_ref,
        physical_state=physical,
        operational_state=operational,
        commercial_state=commercial,
        trust_state=trust,
        recovery_state=recovery,
        effective_state=effective_state,
        reason_codes=all_reasons,
        confidence=round(overall_confidence, 6),
        policy_violations=inp.policy_violations,
        dependency_trace=inp.dependency_trace,
        evidence_refs=inp.evidence_refs,
        supporting_evidence=all_evidence,
        timestamp=inp.timestamp,
    )


def _assess_physical(inp: ClosureInput) -> ClosureLayer:
    reasons: list[str] = []
    if not inp.physically_accessible:
        return ClosureLayer(
            layer="physical",
            state=LayerState.UNAVAILABLE,
            confidence=0.95,
            reason_codes=["physically_inaccessible"],
        )
    if inp.physical_capacity_ratio <= 0.2:
        reasons.append("physical_capacity_severely_constrained")
        return ClosureLayer(
            layer="physical",
            state=LayerState.DEGRADED,
            confidence=0.85,
            reason_codes=reasons,
        )
    return ClosureLayer(
        layer="physical",
        state=LayerState.AVAILABLE,
        confidence=0.9,
        reason_codes=[],
    )


def _assess_operational(inp: ClosureInput) -> ClosureLayer:
    reasons: list[str] = []
    if not inp.navigation_available:
        reasons.append("navigation_unavailable")
    if inp.navigation_trust < 0.5:
        reasons.append("navigation_untrusted")
    if not inp.communications_available:
        reasons.append("communications_unavailable")
    if inp.communications_trust < 0.5:
        reasons.append("communications_degraded")
    if not inp.escort_available:
        reasons.append("escort_unavailable")
    if inp.escort_dependent and not inp.escort_available:
        reasons.append("service_dependent")
    if not inp.weather_safe:
        reasons.append("weather_unsafe")

    if not inp.navigation_available or not inp.communications_available:
        return ClosureLayer(
            layer="operational",
            state=LayerState.UNAVAILABLE,
            confidence=0.9,
            reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="operational",
            state=LayerState.DEGRADED,
            confidence=0.8,
            reason_codes=reasons,
        )
    return ClosureLayer(
        layer="operational",
        state=LayerState.AVAILABLE,
        confidence=0.9,
        reason_codes=[],
    )


def _assess_commercial(inp: ClosureInput) -> ClosureLayer:
    reasons: list[str] = []
    if not inp.insurance_available or inp.insurance_coverage <= 0.1:
        reasons.append("uninsurable")
    if not inp.carrier_capacity_available or inp.carrier_capacity_ratio <= 0.1:
        reasons.append("no_carrier_capacity")
    if inp.commercial_viability <= 0.2:
        reasons.append("commercially_unviable")

    if "uninsurable" in reasons and "no_carrier_capacity" in reasons:
        return ClosureLayer(
            layer="commercial",
            state=LayerState.UNAVAILABLE,
            confidence=0.85,
            reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="commercial",
            state=LayerState.DEGRADED,
            confidence=0.8,
            reason_codes=reasons,
        )
    return ClosureLayer(
        layer="commercial",
        state=LayerState.AVAILABLE,
        confidence=0.85,
        reason_codes=[],
    )


def _assess_trust(inp: ClosureInput) -> ClosureLayer:
    reasons: list[str] = []
    if inp.data_integrity < 0.5:
        reasons.append("data_integrity_low")
    if inp.observation_confidence < 0.5:
        reasons.append("observation_confidence_low")
    if inp.source_diversity < 2:
        reasons.append("insufficient_source_diversity")

    if inp.data_integrity < 0.3 or inp.observation_confidence < 0.3:
        return ClosureLayer(
            layer="trust",
            state=LayerState.UNAVAILABLE,
            confidence=0.7,
            reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="trust",
            state=LayerState.DEGRADED,
            confidence=0.75,
            reason_codes=reasons,
        )
    return ClosureLayer(
        layer="trust",
        state=LayerState.AVAILABLE,
        confidence=0.85,
        reason_codes=[],
    )


def _assess_recovery(inp: ClosureInput) -> ClosureLayer:
    reasons: list[str] = []
    if inp.recovery_backlog_active:
        reasons.append("recovery_backlogged")
        return ClosureLayer(
            layer="recovery",
            state=LayerState.DEGRADED,
            confidence=0.85,
            reason_codes=reasons,
        )
    return ClosureLayer(
        layer="recovery",
        state=LayerState.AVAILABLE,
        confidence=0.95,
        reason_codes=[],
    )


def _derive_effective_state(
    physical: ClosureLayer,
    operational: ClosureLayer,
    commercial: ClosureLayer,
    trust: ClosureLayer,
    recovery: ClosureLayer | None = None,
) -> CorridorState:
    """Derive the effective state from the closure layers."""
    if physical.state == LayerState.UNAVAILABLE:
        return CorridorState.PHYSICALLY_CLOSED

    if operational.state == LayerState.UNAVAILABLE or (
        commercial.state == LayerState.UNAVAILABLE and trust.state == LayerState.UNAVAILABLE
    ):
        return CorridorState.FUNCTIONALLY_CLOSED

    # Check specific degradation patterns
    if "uninsurable" in commercial.reason_codes:
        return CorridorState.OPEN_BUT_UNINSURABLE

    if "no_carrier_capacity" in commercial.reason_codes:
        return CorridorState.OPEN_BUT_NO_CARRIER_CAPACITY

    if "navigation_untrusted" in operational.reason_codes:
        return CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED

    if "communications_degraded" in operational.reason_codes:
        return CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED

    if "service_dependent" in operational.reason_codes:
        return CorridorState.OPEN_BUT_SERVICE_DEPENDENT

    if recovery is not None and "recovery_backlogged" in recovery.reason_codes:
        return CorridorState.RECOVERY_BACKLOGGED

    if physical.state == LayerState.DEGRADED:
        return CorridorState.OPEN_CAPACITY_CONSTRAINED

    if (
        operational.state == LayerState.DEGRADED
        or commercial.state == LayerState.DEGRADED
        or trust.state == LayerState.DEGRADED
        or (recovery is not None and recovery.state == LayerState.DEGRADED)
    ):
        return CorridorState.OPEN_DEGRADED

    if trust.state == LayerState.UNKNOWN:
        return CorridorState.UNKNOWN

    return CorridorState.OPEN
