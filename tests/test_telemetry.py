from __future__ import annotations

import hashlib
import hmac
import time

import orjson
import pytest

from continuityos.domain import AssertionClass, MetricName
from continuityos.telemetry import (
    TelemetryAuthenticationError,
    normalized_operator_observation,
    verify_operator_signature,
)


def test_operator_signature_and_normalization() -> None:
    secret = "s" * 32
    timestamp = str(int(time.time()))
    payload = {
        "tenant_id": "tenant-a",
        "asset_id": "port-a",
        "metric": "cyber_control_health",
        "value": 0.72,
        "unit": "ratio",
        "confidence": 0.94,
        "observed_at": "2026-07-23T12:00:00Z",
        "sequence": 3,
    }
    body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    signature = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    verify_operator_signature(
        body=body,
        timestamp=timestamp,
        signature=f"sha256={signature}",
        secret=secret,
    )
    observation = normalized_operator_observation(payload, body)
    assert observation.metric == MetricName.CYBER_CONTROL_HEALTH
    assert observation.assertion_class == AssertionClass.CYBER_HEALTH
    assert observation.metadata["sequence"] == 3


def test_operator_signature_rejects_bad_or_stale_requests() -> None:
    with pytest.raises(TelemetryAuthenticationError, match="invalid timestamp"):
        verify_operator_signature(body=b"{}", timestamp="bad", signature="x", secret="s" * 32)
    with pytest.raises(TelemetryAuthenticationError, match="outside allowed skew"):
        verify_operator_signature(body=b"{}", timestamp="1", signature="x", secret="s" * 32)
    timestamp = str(int(time.time()))
    with pytest.raises(TelemetryAuthenticationError, match="signature mismatch"):
        verify_operator_signature(body=b"{}", timestamp=timestamp, signature="x", secret="s" * 32)


def test_operator_rejects_public_only_metric() -> None:
    payload = {
        "tenant_id": "tenant-a",
        "asset_id": "sensor-a",
        "sequence": 1,
        "metric": "sea_ice_concentration",
        "value": 0.5,
        "unit": "ratio",
        "observed_at": "2026-07-23T12:00:00Z",
    }
    body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    with pytest.raises(ValueError, match="not accepted"):
        normalized_operator_observation(payload, body)


def test_operator_requires_scope_and_sequence() -> None:
    payload = {
        "metric": "port_availability",
        "value": 0.8,
        "unit": "ratio",
        "observed_at": "2026-07-23T12:00:00Z",
    }
    body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    with pytest.raises(ValueError, match="tenant_id"):
        normalized_operator_observation(payload, body)
