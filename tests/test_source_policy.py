from __future__ import annotations

from datetime import UTC, datetime

import pytest

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    SourceTrust,
)
from continuityos.sources.policy import SourcePolicyError, validate_observation_source


def test_celestrak_cannot_assert_satcom_availability(provenance) -> None:
    observation = Observation(
        source_id="celestrak-gp",
        source_trust=SourceTrust.OPEN_CONTEXT,
        assertion_class=AssertionClass.LIVE_AVAILABILITY,
        metric=MetricName.SATCOM_AVAILABILITY,
        value=1.0,
        unit="ratio",
        observed_at=datetime.now(UTC),
        confidence=0.8,
        provenance=provenance,
    )
    with pytest.raises(SourcePolicyError, match="cannot assert"):
        validate_observation_source(observation)


def test_world_port_index_cannot_assert_live_capacity(provenance) -> None:
    observation = Observation(
        source_id="nga-world-port-index",
        source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        assertion_class=AssertionClass.LIVE_CAPACITY,
        metric=MetricName.PORT_CAPACITY,
        value=0.9,
        unit="ratio",
        observed_at=datetime.now(UTC),
        confidence=0.9,
        provenance=provenance,
    )
    with pytest.raises(SourcePolicyError):
        validate_observation_source(observation)


def test_metric_assertion_mismatch_is_rejected(provenance) -> None:
    observation = Observation(
        source_id="eccc-geomet",
        source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        assertion_class=AssertionClass.ICE,
        metric=MetricName.DATA_INTEGRITY,
        value=1.0,
        unit="ratio",
        observed_at=datetime.now(UTC),
        confidence=0.8,
        provenance=provenance,
    )
    with pytest.raises(SourcePolicyError, match="incompatible"):
        validate_observation_source(observation)


def test_analyst_assessment_requires_epistemic_metadata(provenance) -> None:
    observation = Observation(
        source_id="analyst-assessment",
        source_trust=SourceTrust.ANALYST_ASSESSMENT,
        assertion_class=AssertionClass.GEOPOLITICAL_CONTEXT,
        metric=MetricName.GEOPOLITICAL_PRESSURE,
        value=0.6,
        unit="normalized",
        observed_at=datetime.now(UTC),
        confidence=0.7,
        provenance=provenance,
    )
    with pytest.raises(SourcePolicyError, match="judgment_type"):
        validate_observation_source(observation)


def test_observation_rejects_out_of_range_ratio(provenance) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="normalized"):
        Observation(
            source_id="operator-telemetry",
            source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
            assertion_class=AssertionClass.LIVE_AVAILABILITY,
            metric=MetricName.SATCOM_AVAILABILITY,
            value=75.0,
            unit="percent",
            observed_at=datetime.now(UTC),
            confidence=0.8,
            provenance=provenance,
        )
