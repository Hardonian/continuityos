from __future__ import annotations

from datetime import datetime
from typing import Literal
from xml.etree import ElementTree

from pydantic import BaseModel, ConfigDict, Field

CapabilityStatus = Literal["implemented", "source-consumer", "contract-only", "planned"]


class ContinuityCloudEvent(BaseModel):
    """Structured CloudEvents 1.0 envelope for approved ContinuityOS events."""

    model_config = ConfigDict(extra="allow")

    specversion: Literal["1.0"]
    id: str = Field(min_length=1, max_length=256)
    type: str = Field(min_length=1, max_length=256)
    source: str = Field(min_length=1, max_length=512)
    subject: str | None = Field(default=None, max_length=512)
    time: datetime
    datacontenttype: str = Field(default="application/json", max_length=128)
    data: dict[str, object]


SUPPORTED_CLOUD_EVENT_TYPES = frozenset({"com.continuityos.operator.observation.v1"})


class CAPAlert(BaseModel):
    """Bounded CAP 1.2 alert metadata; no dispatch or retransmission semantics."""

    identifier: str = Field(min_length=1, max_length=256)
    sender: str = Field(min_length=1, max_length=256)
    sent: datetime
    status: str = Field(min_length=1, max_length=64)
    message_type: str = Field(min_length=1, max_length=64)
    scope: str = Field(min_length=1, max_length=64)
    language: str | None = Field(default=None, max_length=32)
    category: str | None = Field(default=None, max_length=64)
    event: str | None = Field(default=None, max_length=256)
    headline: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=4096)
    area_description: str | None = Field(default=None, max_length=1024)
    polygon: str | None = Field(default=None, max_length=4096)


def parse_cap_alert(payload: bytes) -> CAPAlert:
    if len(payload) > 2_000_000:
        raise ValueError("CAP payload exceeds 2 MiB")
    upper_payload = payload.upper()
    if b"<!DOCTYPE" in upper_payload or b"<!ENTITY" in upper_payload:
        raise ValueError("CAP payload cannot contain DOCTYPE or ENTITY declarations")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("invalid CAP XML") from exc

    def text(name: str, parent: ElementTree.Element = root) -> str | None:
        for element in parent.iter():
            if element.tag.rsplit("}", 1)[-1] == name:
                value = (element.text or "").strip()
                return value or None
        return None

    info = next(
        (element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "info"),
        None,
    )
    if info is None:
        raise ValueError("CAP alert has no info block")
    identifier = text("identifier")
    sender = text("sender")
    sent = text("sent")
    status = text("status")
    message_type = text("msgType")
    scope = text("scope")
    if not all((identifier, sender, sent, status, message_type, scope)):
        raise ValueError("CAP alert is missing required metadata")
    assert identifier is not None
    assert sender is not None
    assert sent is not None
    assert status is not None
    assert message_type is not None
    assert scope is not None
    try:
        sent_at = datetime.fromisoformat(sent.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("CAP sent timestamp is invalid") from exc
    return CAPAlert(
        identifier=identifier,
        sender=sender,
        sent=sent_at,
        status=status,
        message_type=message_type,
        scope=scope,
        language=text("language", info),
        category=text("category", info),
        event=text("event", info),
        headline=text("headline", info),
        description=text("description", info),
        area_description=text("areaDesc", info),
        polygon=text("polygon", info),
    )


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
        status="implemented",
        direction="inbound",
        media_types=("application/cloudevents+json",),
        endpoint="/v1/integrations/cloudevents",
        notes=(
            "Signed structured CloudEvents 1.0 are accepted for one approved "
            "operator-observation event type and mapped to the telemetry ledger."
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
        protocol="geojson-evidence-export",
        version="RFC 7946",
        status="implemented",
        direction="outbound",
        media_types=("application/geo+json",),
        endpoint="/v1/ogc/collections/evidence/items",
        notes="Protected bounded read-only GeoJSON feature projection of signed evidence records.",
        authoritative_spec="https://www.rfc-editor.org/rfc/rfc7946",
    ),
    InteroperabilityCapability(
        protocol="geopackage-evidence-export",
        version="1.3",
        status="implemented",
        direction="outbound",
        media_types=("application/geopackage+sqlite3",),
        endpoint="/v1/exports/evidence/geopackage",
        notes=(
            "Protected in-memory GeoPackage snapshot with EPSG:4326 point geometry when available."
        ),
        authoritative_spec="https://www.geopackage.org/spec131/index.html",
    ),
    InteroperabilityCapability(
        protocol="ndjson-evidence-export",
        version="1",
        status="implemented",
        direction="outbound",
        media_types=("application/x-ndjson",),
        endpoint="/v1/exports/evidence/ndjson",
        notes="Deterministic read-only ledger records for data-lake, SIEM, and ITSM staging.",
        authoritative_spec="https://github.com/ndjson/ndjson-spec",
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
        status="implemented",
        direction="inbound",
        media_types=("application/cap+xml", "application/xml"),
        endpoint="/v1/integrations/cap",
        notes=(
            "Protected CAP 1.2 XML metadata ingress with entity/DOCTYPE rejection, "
            "idempotency, lifecycle fields, and evidence-ledger recording."
        ),
        authoritative_spec="https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html",
    ),
    InteroperabilityCapability(
        protocol="decision-packet-api",
        version="1",
        status="implemented",
        direction="outbound",
        media_types=("application/json",),
        endpoint="/v1/decision-packets",
        notes=(
            "Protected single-call assessment, dependency impact, and bounded mitigation "
            "packet with idempotency, evidence recording, and explicit human approval boundary."
        ),
        authoritative_spec="https://github.com/Hardonian/continuityos",
    ),
    InteroperabilityCapability(
        protocol="stac-catalog",
        version="1.0.0",
        status="implemented",
        direction="outbound",
        media_types=("application/json",),
        endpoint="/v1/stac/catalog",
        notes=(
            "Metadata-only STAC catalog for evidence exports; no imagery asset "
            "conformance is claimed."
        ),
        authoritative_spec="https://stacspec.org/en/",
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
