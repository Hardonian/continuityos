# Interoperability Profile and Integration Roadmap

Status: implemented capability manifest plus prioritized integration plan. This is not a conformance certificate.

Machine-readable capability endpoint:

```text
GET /v1/interoperability
```

The endpoint is protected by the ContinuityOS API key and reports whether each protocol is implemented, consumed from a source, contract-only, or planned.

## Why this matters

ContinuityOS should integrate beside existing GIS, emergency-management, sensor, SIEM, observability, and SaaS systems. It should not require those systems to become ContinuityOS customers before they can exchange bounded evidence.

The product boundary is:

```text
existing systems remain authoritative for their own domain
ContinuityOS preserves provenance, dependency context, bounded analysis, and human review
```

## Current capability truth

| Protocol/profile | Status | Direction | Practical use |
|---|---|---|---|
| HMAC operator telemetry JSON | Implemented | Inbound | Signed customer-owned capacity, availability, cyber-health, inventory, insurer, escort, and SATCOM assertions. |
| CloudEvents 1.0 envelope | Implemented | Inbound | Signed `application/cloudevents+json` observation bridge at `/v1/integrations/cloudevents`; one approved event type is mapped into the existing telemetry ledger. |
| OGC API Features 1.0.1 | Source-consumer | Inbound | ECCC/Canadian geospatial source acquisition; ContinuityOS is not claiming to be a conformant feature server. |
| GeoJSON evidence export | Implemented | Outbound | Protected bounded feature projection at `/v1/ogc/collections/evidence/items`. |
| GeoPackage evidence export | Implemented | Outbound | Read-only EPSG:4326 GeoPackage snapshot at `/v1/exports/evidence/geopackage`. |
| NDJSON evidence export | Implemented | Outbound | Deterministic ledger records at `/v1/exports/evidence/ndjson` for data-lake/SIEM/ITSM staging. |
| OGC SensorThings 1.1 | Contract-only | Inbound | Future customer sensor mapping over REST/MQTT without installing a broker by default. |
| STAC API 1.0.0 | Source-consumer | Inbound | Copernicus and earth-observation catalogue discovery. Imagery processing is not implied. |
| STAC metadata catalog | Implemented | Outbound | Metadata-only catalog at `/v1/stac/catalog`; no imagery asset conformance is claimed. |
| Common Alerting Protocol 1.2 | Implemented | Inbound | Protected `/v1/integrations/cap` parser with alert lifecycle/area preservation; no dispatch or retransmission. |
| OTLP/HTTP | Planned | Outbound | Export service traces/metrics/logs to an existing OpenTelemetry Collector. Current `/metrics` remains Prometheus text. |

## Highest-ROI sequence

### Completed: CloudEvents profile and signed webhook bridge

Priority: highest.

Why:

- Connects n8n, Azure Event Grid, AWS EventBridge, Google Eventarc, Kafka bridges, NATS, and ordinary webhooks through one envelope.
- Preserves `specversion`, `id`, `type`, `source`, `subject`, `time`, and content type.
- Allows downstream systems to consume continuity events without importing the full ContinuityOS data model.

Required implementation:

- Accept `application/cloudevents+json`.
- Keep HMAC/mTLS/API-key authentication outside the CloudEvent envelope.
- Require idempotency by CloudEvent `id` plus tenant scope.
- Map only approved event types to operator telemetry or evidence records.
- Reject unknown event types rather than silently treating arbitrary events as truth.
- Emit signed/hashed evidence references, not raw sensitive customer data by default.

Authoritative specification:

- https://github.com/cloudevents/spec/blob/v1.0/spec.md
- https://github.com/cloudevents/spec/blob/v1.0/http-protocol-binding.md

### Completed: OGC-style evidence export profile

Priority: highest for GIS and disconnected operations.

Why:

- Integrates with QGIS, ArcGIS, GeoServer, GDAL, and other GIS systems.
- GeoPackage is useful for field/offline exchange.
- Avoids forcing customers into a proprietary graph or API.

Implemented controls:

- Publish a protected read-only OGC-style profile for one evidence collection.
- Implement `/v1/ogc/collections` and `/v1/ogc/collections/{id}/items`.
- Export only approved evidence/feature classes, not raw private telemetry by default.
- Provide GeoJSON and GeoPackage bundles with manifest, snapshot IDs, timestamps, CRS, licence, tenant scope, and retention metadata.
- Do not claim OGC conformance until an external conformance test is run.

Authoritative specification:

- https://www.ogc.org/standards/ogcapi-features/
- https://www.ogc.org/standards/geopackage/

### 4. OGC SensorThings customer adapter

Priority: high after one authorized pilot.

Why:

- A standards-based path for SCADA-adjacent, environmental, port, facility, and edge sensor observations.
- REST and MQTT options allow integration with existing sensor gateways.

Required implementation:

- Inbound read-only adapter first; do not add tasking/actuation.
- Map Thing, Location, Sensor, Datastream, Observation, and ObservedProperty to normalized observations.
- Preserve sensor system identity, units, phenomenon time, result time, QC, and customer tenant scope.
- Support pagination and `$filter`/time-window bounds.
- Add MQTT only through an existing customer broker or managed bridge; do not install an always-on broker by default.

Authoritative specification:

- https://www.ogc.org/standards/sensorthings/
- https://docs.ogc.org/is/18-088/18-088.html

### 5. OpenTelemetry Collector export

Priority: medium/high for enterprise operations.

Why:

- Existing customers may already have Grafana, Prometheus, Elastic, Splunk, Datadog, or an OpenTelemetry Collector.
- A Collector avoids shipping vendor SDKs or credentials into ContinuityOS.

Required implementation:

- Prefer OTLP/HTTP export to a customer-provided Collector endpoint.
- Make export opt-in and fail-soft; never block core evidence ingestion.
- Redact tenant-sensitive fields and customer payloads.
- Emit service health, adapter latency, cache hits/misses, source freshness, rejected authentication, and evidence verification metrics.
- Keep Prometheus `/metrics` compatibility.

Authoritative specification:

- https://opentelemetry.io/docs/specs/otlp/

### 6. SIEM and ITSM bridges

Priority: medium, after CloudEvents.

Recommended patterns:

- CloudEvents to existing webhook/event buses.
- CEF/LEEF/syslog output only for carefully selected security-health summaries.
- ServiceNow/Jira/incident-management integration through customer-owned outbound webhooks.
- No automatic incident creation for uncertain public alerts without a customer policy.

### 7. Data catalogue and exchange metadata

Priority: medium.

Add:

- DCAT-AP/JSON-LD metadata for datasets and snapshots.
- CSV/JSON/GeoJSON/GeoPackage export.
- Parquet only when a real analytical workload justifies the dependency.
- Signed manifest references when KMS/HSM custody exists.

Do not claim DCAT-AP or OGC conformance until a validator/conformance test passes.

## Integration contract rules

Every adapter must define:

- inbound/outbound direction;
- protocol and version;
- authentication and authorization;
- tenant boundary;
- idempotency key;
- replay protection;
- pagination/window limits;
- timeout/retry/backoff;
- source authority and licence;
- timestamp and timezone rules;
- unit and CRS rules;
- quality/review state;
- raw payload retention;
- deletion/retention behavior;
- failure mode;
- rollback and disable switch;
- conformance or fixture test;
- live smoke evidence when credentials/authorization exist.

## What not to do

- Do not install Kafka, MQTT, NATS, Elasticsearch, or a full SIEM just to claim integration.
- Do not expose raw customer telemetry to public GIS endpoints.
- Do not turn CloudEvents into an unauthenticated command channel.
- Do not add tasking/actuation to SensorThings in the first interoperability release.
- Do not claim “fully interoperable” from a manifest alone.
- Do not claim ArcGIS, ServiceNow, Splunk, AWS, Azure, NATO, government, or port integration without a tested authorized endpoint.
- Do not use STAC metadata as proof that image-derived events were detected.

## Recommended next build tranche

1. Implement the signed CloudEvents observation bridge with fixture tests.
2. Implement CAP 1.2 inbound parsing and ECCC/CAP semantic comparison tests.
3. Add read-only OGC API Features/GeoJSON export for a non-sensitive evidence collection.
4. Add GeoPackage bundle generation and offline verification.
5. Add opt-in OTLP exporter targeting a customer Collector.
6. Run one authorized pilot against a real customer webhook or SensorThings endpoint.
7. Only then add vendor-specific connectors.
