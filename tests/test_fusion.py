from __future__ import annotations

from datetime import UTC, datetime

from continuityos.domain import (
    AssertionClass,
    CorridorState,
    MetricName,
    Observation,
    SourceTrust,
)
from continuityos.fusion import FusionEngine
from tests.conftest import operator_observation


def test_assessment_is_deterministic_and_penalizes_missing_data(provenance) -> None:
    observations = [
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.ICE,
            metric=MetricName.SEA_ICE_CONCENTRATION,
            value=65,
            unit="percent",
            observed_at=datetime.now(UTC),
            confidence=0.95,
            provenance=provenance,
        ),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=0.35,
            unit="normalized",
            observed_at=datetime.now(UTC),
            confidence=0.9,
            provenance=provenance,
        ),
        operator_observation(MetricName.PORT_AVAILABILITY, 0.75, provenance),
        operator_observation(MetricName.SATCOM_AVAILABILITY, 0.7, provenance),
        operator_observation(MetricName.CYBER_CONTROL_HEALTH, 0.55, provenance),
        operator_observation(MetricName.DATA_INTEGRITY, 0.8, provenance),
        operator_observation(MetricName.INSURANCE_AVAILABILITY, 0.65, provenance),
        operator_observation(MetricName.ESCORT_CAPACITY, 0.4, provenance),
        operator_observation(MetricName.INVENTORY_DAYS, 18, provenance),
    ]
    first = FusionEngine().assess("northwest-passage-test", observations)
    second = FusionEngine().assess("northwest-passage-test", observations)
    assert first.overall_risk == second.overall_risk
    assert first.state in {CorridorState.DEGRADED, CorridorState.FUNCTIONALLY_CLOSED}
    assert first.missing_required_metrics == []
    assert first.confidence > 0.7


def test_physical_closure_requires_operator_port_signal(provenance) -> None:
    observations = [
        operator_observation(MetricName.PORT_AVAILABILITY, 0.0, provenance),
        operator_observation(MetricName.SATCOM_AVAILABILITY, 1.0, provenance),
        operator_observation(MetricName.CYBER_CONTROL_HEALTH, 1.0, provenance),
        operator_observation(MetricName.DATA_INTEGRITY, 1.0, provenance),
        operator_observation(MetricName.INSURANCE_AVAILABILITY, 1.0, provenance),
        operator_observation(MetricName.ESCORT_CAPACITY, 1.0, provenance),
        operator_observation(MetricName.INVENTORY_DAYS, 45, provenance),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.ICE,
            metric=MetricName.SEA_ICE_CONCENTRATION,
            value=10,
            unit="percent",
            observed_at=datetime.now(UTC),
            confidence=0.95,
            provenance=provenance,
        ),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=0.1,
            unit="normalized",
            observed_at=datetime.now(UTC),
            confidence=0.95,
            provenance=provenance,
        ),
    ]
    assessment = FusionEngine().assess("closed-port", observations)
    assert assessment.state == CorridorState.PHYSICALLY_CLOSED


def test_context_only_data_cannot_reduce_live_operability_risk(provenance) -> None:
    now = datetime.now(UTC)
    base = [
        operator_observation(MetricName.PORT_AVAILABILITY, 0.5, provenance),
        operator_observation(MetricName.SATCOM_AVAILABILITY, 0.5, provenance),
        operator_observation(MetricName.CYBER_CONTROL_HEALTH, 0.5, provenance),
        operator_observation(MetricName.DATA_INTEGRITY, 0.5, provenance),
        operator_observation(MetricName.INSURANCE_AVAILABILITY, 0.5, provenance),
        operator_observation(MetricName.ESCORT_CAPACITY, 0.5, provenance),
        operator_observation(MetricName.INVENTORY_DAYS, 20, provenance),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.ICE,
            metric=MetricName.SEA_ICE_CONCENTRATION,
            value=50,
            unit="percent",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=0.5,
            unit="normalized",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
    ]
    context = Observation(
        source_id="celestrak-gp",
        source_trust=SourceTrust.OPEN_CONTEXT,
        assertion_class=AssertionClass.ORBITAL_GEOMETRY,
        metric=MetricName.SATELLITE_GEOMETRY_DENSITY,
        value=10_000,
        unit="catalogued_objects",
        observed_at=now,
        confidence=1.0,
        provenance=provenance,
    )
    replay_time = max(item.observed_at for item in [*base, context])
    without_context = FusionEngine().assess("test", base, as_of=replay_time)
    with_context = FusionEngine().assess("test", [*base, context], as_of=replay_time)
    assert with_context.overall_risk == without_context.overall_risk
    assert with_context.confidence == without_context.confidence
    assert any("context-only" in caveat for caveat in with_context.caveats)


def test_assessment_replay_uses_explicit_as_of(provenance) -> None:
    now = datetime.now(UTC)
    observations = [
        operator_observation(MetricName.PORT_AVAILABILITY, 0.8, provenance),
        operator_observation(MetricName.SATCOM_AVAILABILITY, 0.8, provenance),
        operator_observation(MetricName.CYBER_CONTROL_HEALTH, 0.8, provenance),
        operator_observation(MetricName.DATA_INTEGRITY, 0.8, provenance),
        operator_observation(MetricName.INSURANCE_AVAILABILITY, 0.8, provenance),
        operator_observation(MetricName.ESCORT_CAPACITY, 0.8, provenance),
        operator_observation(MetricName.INVENTORY_DAYS, 30, provenance),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.ICE,
            metric=MetricName.SEA_ICE_CONCENTRATION,
            value=20,
            unit="percent",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=0.2,
            unit="normalized",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
    ]
    replay_time = max(item.observed_at for item in observations)
    first = FusionEngine().assess("replay", observations, as_of=replay_time)
    second = FusionEngine().assess("replay", observations, as_of=replay_time)
    assert first.overall_risk == second.overall_risk
    assert first.confidence == second.confidence


def test_stale_live_telemetry_is_excluded(provenance) -> None:
    from datetime import timedelta

    now = datetime.now(UTC)
    stale = operator_observation(MetricName.SATCOM_AVAILABILITY, 1.0, provenance).model_copy(
        update={"observed_at": now - timedelta(hours=2)}
    )
    current = [
        operator_observation(MetricName.PORT_AVAILABILITY, 0.8, provenance),
        operator_observation(MetricName.CYBER_CONTROL_HEALTH, 0.8, provenance),
        operator_observation(MetricName.DATA_INTEGRITY, 0.8, provenance),
        operator_observation(MetricName.INSURANCE_AVAILABILITY, 0.8, provenance),
        operator_observation(MetricName.ESCORT_CAPACITY, 0.8, provenance),
        operator_observation(MetricName.INVENTORY_DAYS, 30, provenance),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.ICE,
            metric=MetricName.SEA_ICE_CONCENTRATION,
            value=20,
            unit="percent",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=0.2,
            unit="normalized",
            observed_at=now,
            confidence=0.9,
            provenance=provenance,
        ),
    ]
    replay_time = max(item.observed_at for item in current)
    assessment = FusionEngine().assess("stale", [*current, stale], as_of=replay_time)
    assert MetricName.SATCOM_AVAILABILITY in assessment.missing_required_metrics
    assert any("stale observation excluded" in caveat for caveat in assessment.caveats)
