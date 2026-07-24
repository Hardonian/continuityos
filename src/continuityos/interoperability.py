from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CapabilityStatus = Literal["implemented", "source-consumer", "contract-only", "planned"]


class InteroperabilityCapability(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol: str = Field(min_length=2, max_length=64)
    version: str = Field(min_length=1, max_length=32)
    status: CapabilityStatus
    direction: Literal["inbound", "outbound", "bidirectional"]
    media_types: tuple[str, ...] = ()
    endpoint: str | None = None
    notes: str = Field(min_length=1, max_length=512)
    authoritative_spec: str = Field(min_length=8, max_length=512)


INTEROPERABILITY_CAPABILITIES: tuple[InteroperabilityCapability, ...] = (
    InteroperabilityCapability(
        protocol="operator-telemetry-hmac-json",
        version="1",
        status="implemented",
        direction="inbound",
        media_types=("application/json",),
        endpoint="/v1/operator-observations",
        notes="Tenant/asset/sequence-scoped signed observations with replay rejection.",
        authoritative_spec="https://www.rfc-editor.org/rfc/rfc2104",
    ),
    InteroperabilityCapability(
        protocol="cloud-events",
        version="1.0",
        status="contract-only",
        direction="bidirectional",
        media_types=("application/cloudevents+json",),
        endpoint="/v1/integrations/cloudevents",
        notes=(
            "Envelope profile is reserved for signed operator observations; "
            "vendor adapters must preserve event id/source/time."
        ),
        authoritative_spec="https://github.com/cloudevents/spec/blob/v1.0/spec.md",
    ),
    InteroperabilityCapability(
        protocol="ogc-api-features",
        version="1.0.1",
        status="source-consumer",
        direction="inbound",
        media_types=("application/geo+json", "application/json"),
        notes=(
            "Used for governed source acquisition; ContinuityOS is not claiming "
            "a conformant feature-server implementation."
        ),
        authoritative_spec="https://www.ogc.org/standards/ogcapi-features/",
    ),
    InteroperabilityCapability(
        protocol="ogc-sensorthings",
        version="1.1",
        status="contract-only",
        direction="inbound",
        media_types=("application/json",),
        notes=(
            "Customer sensor mapping is defined but no MQTT broker or "
            "SensorThings server is installed by default."
        ),
        authoritative_spec="https://www.ogc.org/standards/sensorthings/",
    ),
    InteroperabilityCapability(
        protocol="stac-api",
        version="1.0.0",
        status="source-consumer",
        direction="inbound",
        media_types=("application/json", "application/geo+json"),
        notes=(
            "Copernicus/STAC metadata is consumed as discoverable context; "
            "imagery processing is not implied."
        ),
        authoritative_spec="https://www.ogc.org/standards/stac/",
    ),
    InteroperabilityCapability(
        protocol="common-alerting-protocol",
        version="1.2",
        status="planned",
        direction="inbound",
        media_types=("application/cap+xml", "application/xml"),
        notes=(
            "CAP profile is the next alert-ingress adapter; current ECCC GeoMet "
            "JSON normalization remains available."
        ),
        authoritative_spec="https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html",
    ),
    InteroperabilityCapability(
        protocol="opentelemetry-otlp-http",
        version="1.0",
        status="planned",
        direction="outbound",
        media_types=("application/json", "application/x-protobuf"),
        endpoint="/v1/metrics",
        notes=(
            "Current metrics endpoint is Prometheus text; OTLP export requires "
            "an explicit collector/exporter decision."
        ),
        authoritative_spec="https://opentelemetry.io/docs/specs/otlp/",
    ),
)


def interoperability_manifest() -> dict[str, object]:
    return {
        "name": "ContinuityOS interoperability profile",
        "profile_version": "2026-07-23",
        "claim_boundary": (
            "This manifest reports implemented boundaries and explicitly labels "
            "source-consumer, contract-only, and planned capabilities. It is not "
            "a conformance certificate."
        ),
        "capabilities": [item.model_dump(mode="json") for item in INTEROPERABILITY_CAPABILITIES],
    }
