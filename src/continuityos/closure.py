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

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import CorridorState, Score


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
    effective_state: CorridorState
    reason_codes: list[str]
    confidence: Score
    supporting_evidence: list[str] = Field(default_factory=list)


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


def assess_closure(inp: ClosureInput) -> ClosureAssessment:
    """Assess functional closure of a resource across all four layers."""
    physical = _assess_physical(inp)
    operational = _assess_operational(inp)
    commercial = _assess_commercial(inp)
    trust = _assess_trust(inp)

    effective_state = _derive_effective_state(physical, operational, commercial, trust)
    all_reasons = (
        physical.reason_codes
        + operational.reason_codes
        + commercial.reason_codes
        + trust.reason_codes
    )
    all_evidence = (
        physical.supporting_evidence
        + operational.supporting_evidence
        + commercial.supporting_evidence
        + trust.supporting_evidence
    )
    confidences = [
        physical.confidence, operational.confidence,
        commercial.confidence, trust.confidence,
    ]
    overall_confidence = min(confidences) if confidences else 0.0

    return ClosureAssessment(
        resource_ref=inp.resource_ref,
        physical_state=physical,
        operational_state=operational,
        commercial_state=commercial,
        trust_state=trust,
        effective_state=effective_state,
        reason_codes=all_reasons,
        confidence=round(overall_confidence, 6),
        supporting_evidence=all_evidence,
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
            layer="physical", state=LayerState.DEGRADED,
            confidence=0.85, reason_codes=reasons,
        )
    return ClosureLayer(
        layer="physical", state=LayerState.AVAILABLE,
        confidence=0.9, reason_codes=[],
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
    if not inp.weather_safe:
        reasons.append("weather_unsafe")

    if not inp.navigation_available or not inp.communications_available:
        return ClosureLayer(
            layer="operational", state=LayerState.UNAVAILABLE,
            confidence=0.9, reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="operational", state=LayerState.DEGRADED,
            confidence=0.8, reason_codes=reasons,
        )
    return ClosureLayer(
        layer="operational", state=LayerState.AVAILABLE,
        confidence=0.9, reason_codes=[],
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
            layer="commercial", state=LayerState.UNAVAILABLE,
            confidence=0.85, reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="commercial", state=LayerState.DEGRADED,
            confidence=0.8, reason_codes=reasons,
        )
    return ClosureLayer(
        layer="commercial", state=LayerState.AVAILABLE,
        confidence=0.85, reason_codes=[],
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
            layer="trust", state=LayerState.UNAVAILABLE,
            confidence=0.7, reason_codes=reasons,
        )
    if reasons:
        return ClosureLayer(
            layer="trust", state=LayerState.DEGRADED,
            confidence=0.75, reason_codes=reasons,
        )
    return ClosureLayer(
        layer="trust", state=LayerState.AVAILABLE,
        confidence=0.85, reason_codes=[],
    )


def _derive_effective_state(
    physical: ClosureLayer,
    operational: ClosureLayer,
    commercial: ClosureLayer,
    trust: ClosureLayer,
) -> CorridorState:
    """Derive the effective state from the four closure layers."""
    if physical.state == LayerState.UNAVAILABLE:
        return CorridorState.PHYSICALLY_CLOSED

    if (
        operational.state == LayerState.UNAVAILABLE
        or (commercial.state == LayerState.UNAVAILABLE and trust.state == LayerState.UNAVAILABLE)
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

    if physical.state == LayerState.DEGRADED:
        return CorridorState.OPEN_CAPACITY_CONSTRAINED

    if (
        operational.state == LayerState.DEGRADED
        or commercial.state == LayerState.DEGRADED
        or trust.state == LayerState.DEGRADED
    ):
        return CorridorState.OPEN_DEGRADED

    if trust.state == LayerState.UNKNOWN:
        return CorridorState.UNKNOWN

    return CorridorState.OPEN
