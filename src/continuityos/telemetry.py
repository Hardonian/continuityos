from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Any

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)


class TelemetryAuthenticationError(ValueError):
    pass


def verify_operator_signature(
    *,
    body: bytes,
    timestamp: str,
    signature: str,
    secret: str,
    maximum_skew_seconds: int = 300,
) -> None:
    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise TelemetryAuthenticationError("invalid timestamp") from exc
    if abs(int(time.time()) - timestamp_value) > maximum_skew_seconds:
        raise TelemetryAuthenticationError("timestamp outside allowed skew")
    signed = f"{timestamp}.".encode() + body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise TelemetryAuthenticationError("signature mismatch")


def normalized_operator_observation(payload: dict[str, Any], body: bytes) -> Observation:
    tenant_id = payload.get("tenant_id")
    asset_id = payload.get("asset_id")
    sequence = payload.get("sequence")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("operator telemetry requires tenant_id")
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("operator telemetry requires asset_id")
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("operator telemetry requires a non-negative integer sequence")
    metric = MetricName(str(payload["metric"]))
    assertion_map = {
        MetricName.PORT_CAPACITY: AssertionClass.LIVE_CAPACITY,
        MetricName.PORT_AVAILABILITY: AssertionClass.LIVE_AVAILABILITY,
        MetricName.SATCOM_AVAILABILITY: AssertionClass.LIVE_AVAILABILITY,
        MetricName.CYBER_CONTROL_HEALTH: AssertionClass.CYBER_HEALTH,
        MetricName.DATA_INTEGRITY: AssertionClass.CYBER_HEALTH,
        MetricName.INSURANCE_AVAILABILITY: AssertionClass.INSURANCE_ACCESS,
        MetricName.ESCORT_CAPACITY: AssertionClass.LIVE_CAPACITY,
        MetricName.INVENTORY_DAYS: AssertionClass.LIVE_CAPACITY,
    }
    try:
        assertion_class = assertion_map[metric]
    except KeyError as exc:
        raise ValueError(f"operator telemetry metric not accepted: {metric}") from exc
    observed_at = datetime.fromisoformat(str(payload["observed_at"]).replace("Z", "+00:00"))
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    return Observation(
        source_id="operator-telemetry",
        source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
        assertion_class=assertion_class,
        metric=metric,
        value=float(payload["value"]),
        unit=str(payload["unit"]),
        observed_at=observed_at,
        confidence=float(payload.get("confidence", 0.95)),
        provenance=Provenance(
            uri=f"operator://{tenant_id}/{asset_id}",
            content_sha256=hashlib.sha256(body).hexdigest(),
            licence="customer-controlled",
        ),
        metadata={
            "tenant_id": tenant_id,
            "asset_id": asset_id,
            "sequence": sequence,
        },
    )
