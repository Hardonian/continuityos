# Deployment

## Reference deployment

The included container runs a single stateless API process with a local append-only evidence file and snapshot volume. This is suitable for evaluation only.

## Production topology

- private or sovereign Kubernetes cluster;
- API behind an authenticated gateway;
- Postgres for tenant metadata, replay protection, and indexed evidence references;
- immutable object storage for snapshots;
- HSM or cloud KMS for evidence signing;
- customer-controlled secrets manager;
- message queue for ingestion and compilation jobs;
- OpenTelemetry logs, metrics, and traces;
- outbound allow-list proxy;
- WORM evidence replication;
- offline export/import path for disconnected regions.

## Security controls

- run as non-root;
- read-only root filesystem;
- drop Linux capabilities;
- no outbound internet by default;
- mTLS for operator telemetry in addition to HMAC;
- OIDC plus attribute-based authorization;
- per-tenant envelope encryption;
- base images pinned by digest, signed container images, and SBOM;
- admission policies;
- vulnerability scanning;
- disaster-recovery tests;
- restore validation;
- evidence verification as a readiness check.

## Production gaps intentionally exposed

- local durable anti-replay/idempotency state is single-deployment only; a distributed store is required for multiple workers;
- no multi-tenant database or row-level security;
- no distributed ledger locking across independent database nodes;
- no HSM integration;
- no classified-data handling controls;
- no live operational data licences or customer connectors;
- no validated local-route navigation model;
- no insurer, charter, or carrier market feeds;
- no customer-selected data residency, retention, or deletion policy;
- no independent strategic, legal, export-control, safety, or accreditation decision.

These gaps are not hidden behind placeholders; they are the next implementation boundary.
