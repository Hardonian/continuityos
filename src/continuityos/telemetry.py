from __future__ import annotations

import hashlib
import hmac
import struct
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)


class TelemetryAuthenticationError(ValueError):
    pass


class ThreatIndicatorType(str, Enum):
    GPS_SPOOFING = "gps_spoofing"
    RF_JAMMING = "rf_jamming"
    UNAUTHORIZED_DRONE = "unauthorized_drone"
    KINEMATIC_ANOMALY = "kinematic_anomaly"


class DroneKinematics(BaseModel):
    """Schema for UAV and drone kinematic telemetry."""
    drone_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_m: float
    velocity_mps: float
    heading_deg: float = Field(..., ge=0, le=360)
    signal_strength_dbm: float
    timestamp: datetime


class ThreatIndicator(BaseModel):
    """Schema for drone/anti-drone surveillance threats."""
    indicator_type: ThreatIndicatorType
    confidence: float = Field(..., ge=0.0, le=1.0)
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    detected_at: datetime


class TelemetryParser:
    """Parses binary telemetry payloads optimized for ESP32/IoT edge nodes."""
    
    @staticmethod
    def parse_binary_kinematics(payload: bytes) -> DroneKinematics:
        """
        Parse a dense binary payload (e.g. 36 bytes) from an ESP32.
        Format (Little Endian):
        - drone_id (8 bytes string)
        - latitude (float32)
        - longitude (float32)
        - altitude_m (float32)
        - velocity_mps (float32)
        - heading_deg (float32)
        - signal_strength_dbm (float32)
        - timestamp (uint32 epoch)
        """
        if len(payload) < 36:
            raise ValueError(f"Payload too short for kinematics: {len(payload)} bytes")
            
        drone_id_bytes, lat, lon, alt, vel, hdg, sig, ts = struct.unpack("<8sffffffI", payload[:36])
        
        return DroneKinematics(
            drone_id=drone_id_bytes.decode('utf-8').strip('\x00'),
            latitude=lat,
            longitude=lon,
            altitude_m=alt,
            velocity_mps=vel,
            heading_deg=hdg,
            signal_strength_dbm=sig,
            timestamp=datetime.fromtimestamp(ts, tz=UTC)
        )
        
    @staticmethod
    def detect_anomalies(kinematics_stream: list[DroneKinematics]) -> list[ThreatIndicator]:
        """Detect anomalies such as GPS spoofing or RF jamming across a stream."""
        threats = []
        if not kinematics_stream:
            return threats
            
        # Example Anomaly Rule 1: Sudden drop in signal strength could indicate RF Jamming
        for k in kinematics_stream:
            if k.signal_strength_dbm < -100.0:
                threats.append(
                    ThreatIndicator(
                        indicator_type=ThreatIndicatorType.RF_JAMMING,
                        confidence=0.85,
                        latitude=k.latitude,
                        longitude=k.longitude,
                        description=f"Critical signal drop to {k.signal_strength_dbm} dBm",
                        detected_at=k.timestamp
                    )
                )
                
        # Example Anomaly Rule 2: Unrealistic velocity indicates GPS Spoofing
        for k in kinematics_stream:
            if k.velocity_mps > 300.0: # Mach 1+ drone is unlikely
                threats.append(
                    ThreatIndicator(
                        indicator_type=ThreatIndicatorType.GPS_SPOOFING,
                        confidence=0.99,
                        latitude=k.latitude,
                        longitude=k.longitude,
                        description=f"Unrealistic velocity detected: {k.velocity_mps} m/s",
                        detected_at=k.timestamp
                    )
                )
                
        return threats


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
