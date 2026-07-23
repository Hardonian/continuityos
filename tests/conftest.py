from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)


@pytest.fixture
def provenance() -> Provenance:
    body = b"fixture"
    return Provenance(
        uri="fixture://observation",
        retrieved_at=datetime.now(UTC),
        content_sha256=hashlib.sha256(body).hexdigest(),
        snapshot_id="fixture",
        licence="test",
    )


def operator_observation(metric: MetricName, value: float, provenance: Provenance) -> Observation:
    assertion = {
        MetricName.PORT_AVAILABILITY: AssertionClass.LIVE_AVAILABILITY,
        MetricName.SATCOM_AVAILABILITY: AssertionClass.LIVE_AVAILABILITY,
        MetricName.CYBER_CONTROL_HEALTH: AssertionClass.CYBER_HEALTH,
        MetricName.DATA_INTEGRITY: AssertionClass.CYBER_HEALTH,
        MetricName.INSURANCE_AVAILABILITY: AssertionClass.INSURANCE_ACCESS,
        MetricName.ESCORT_CAPACITY: AssertionClass.LIVE_CAPACITY,
        MetricName.INVENTORY_DAYS: AssertionClass.LIVE_CAPACITY,
    }[metric]
    return Observation(
        source_id="operator-telemetry",
        source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
        assertion_class=assertion,
        metric=metric,
        value=value,
        unit="ratio" if metric != MetricName.INVENTORY_DAYS else "days",
        observed_at=datetime.now(UTC),
        confidence=0.95,
        provenance=provenance,
    )
