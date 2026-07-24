# Customer Telemetry and Labelled-Outcome Intake Contract

Status: implementation contract for controlled pilots. It is not evidence that a customer has authorized data access.

## Customer-owned telemetry endpoint

Route:

```text
POST /v1/telemetry/operator
```

Required headers:

```text
X-Continuity-Timestamp: <unix-seconds>
X-Continuity-Signature: sha256=<HMAC-SHA256(timestamp + "." + exact-request-body)>
X-Continuity-API-Key: <operator API key>
```

Required JSON fields:

```json
{
  "tenant_id": "customer-controlled-tenant",
  "asset_id": "customer-controlled-asset",
  "sequence": 1,
  "metric": "port_availability",
  "value": 0.97,
  "unit": "ratio",
  "observed_at": "2026-07-23T20:00:00Z",
  "confidence": 0.95
}
```

Accepted metric values are defined by the service's `MetricName` enum. The service maps them to bounded assertion classes; it does not accept arbitrary intelligence or command data.

## Required customer authorization record before production use

A customer pilot must provide, outside this repository:

- legal entity and authorized data owner;
- written purpose and permitted use;
- tenant and asset namespace;
- data fields and units;
- source system and lawful collection basis;
- retention period and deletion procedure;
- geographic/jurisdictional handling;
- cross-border transfer decision;
- subprocessor/cloud decision;
- incident and revocation contact;
- whether data may be used for model development or only the customer's own analysis;
- whether the customer permits derived aggregate indicators;
- acceptance of the non-authoritative decision-support boundary.

No customer identity, secret, connection string, private telemetry, or authorization document is present in this repository.

## Labelled-outcome intake

A labelled dataset may be submitted to `/v1/analysis/regression` only after the customer or authoritative publisher provides:

- dataset ID and version;
- target definition and measurement procedure;
- target owner and authorization;
- time zone and temporal resolution;
- source snapshot IDs for every row;
- feature normalization methods;
- missingness policy;
- quality flags;
- review state per row;
- holdout boundary chosen before analysis;
- licence/retention statement;
- target leakage review;
- correction/revision procedure.

The request contract now includes:

- `normalization_method`
- `quality_flags`
- `review_state`
- `label_definition`
- `dataset_licence`

Allowed review states:

```text
unreviewed
analyst_reviewed
approved_for_pilot
```

`approved_for_pilot` is a data-governance state supplied by an authorized human reviewer. It is not automatically granted by the API and does not mean operational accreditation.

## Safe pilot sequence

1. Import a small customer-approved sample into an isolated test data directory.
2. Validate schema and signatures.
3. Verify sequence replay rejection.
4. Verify tenant/asset identifiers are present and stable.
5. Run normalization and missingness checks.
6. Freeze the temporal holdout boundary.
7. Run analysis with human review.
8. Record results and limitations in the evidence ledger.
9. Delete the sample when the approved retention period ends.
10. Revoke the customer secret and confirm failed authentication.

## Current implementation truth

Implemented:

- HMAC timestamp verification.
- Tenant/asset/sequence validation.
- Replay rejection through persistent sequence state.
- Snapshot/provenance-bearing regression rows.
- Temporal holdout ridge regression.
- Explicit quality/review/normalization metadata.

Not implemented as production-grade controls:

- Distributed tenant isolation.
- External identity/RBAC.
- HSM/KMS secret or signing custody.
- Customer self-service deletion/export portal.
- Independent privacy/security assessment.
- Customer authorization workflow.
- Real customer-labelled outcome data.

Until those gates are completed, the service remains a single-deployment reference/pilot implementation.
