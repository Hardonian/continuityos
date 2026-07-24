# ContinuityOS Reference Implementation

Cyber-physical continuity assurance for critical maritime, Arctic, port, satellite, and supply-corridor dependencies.

This repository is an executable reference architecture, not a military command system and not an autonomous controller. It ingests bounded observations, enforces source-assertion policy, estimates corridor operability, maps cyber failures to physical supply consequences, compiles a cost-constrained continuity plan, and writes tamper-evident decision evidence.

## What is implemented

- **Source assertion policy:** source, metric, and assertion-class combinations are enforced; public orbital, port, imagery, climate, and traffic data cannot assert live cyber health, service availability, capacity, or insurance access.
- **Immutable open-data snapshots:** content-addressed cache with hashes, retrieval metadata, and atomic writes.
- **Deterministic fusion engine:** explicit replay time, factor-level risk, confidence, freshness decay, missing-data penalties, context-only exclusions, and explicit caveats.
- **Functional closure classification:** open, degraded, functionally closed, or physically closed.
- **Cyber-physical dependency graph:** downstream blast radius, provider concentration, substitution attenuation, and single-point-of-failure detection.
- **Continuity compiler:** exact bounded deterministic action selection under budget, prerequisites, incompatibilities, and human-approval controls.
- **Evidence ledger:** append-only SHA-256 chain with optional Ed25519 signing and verification.
- **Authenticated telemetry:** HMAC-SHA256 canonical webhook for operator assertions.
- **FastAPI service and CLI:** documented endpoints, health checks, source registry, assessment, graph analysis, plan compilation, evidence verification, snapshot import, and key generation.
- **Offline-first controls:** outbound HTTP disabled by default; cached snapshots remain reproducible without network access.

## Why this is different

Most systems stop at alerts, maps, or route recommendations. ContinuityOS connects:

```text
source-qualified observation
→ cyber-physical dependency impact
→ operational corridor state
→ feasible mitigation set
→ costed continuity plan
→ signed decision and outcome evidence
```

The reference implementation makes that chain testable and deterministic. The defensible product moat would come from validated customer dependency graphs, operator telemetry integrations, decision-outcome history, policy packs, and accreditation—not from public datasets alone.

## Safety and authority boundary

ContinuityOS does **not**:

- control vessels, ports, operational technology, drones, weapons, or security assets;
- generate targeting, interdiction, or offensive cyber plans;
- treat public satellite catalogues as proof of communications availability;
- infer current port capacity from static geospatial records;
- claim state intent from public events;
- execute consequential mitigations without accountable human approval.

## Quick start

### Local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make verify
make demo
uvicorn continuityos.service:app --host 127.0.0.1 --port 8080
```

### Docker

```bash
bash scripts/docker_bootstrap.sh
docker compose build
docker compose up
curl http://127.0.0.1:8080/healthz
```

The container has no outbound data access unless `CONTINUITYOS_OUTBOUND_HTTP_ENABLED=true` is explicitly set.

## Live reference deployment

The current EPYC-hosted reference surface is available at `https://aiautomatedsystems.ca/continuityos/`.
It is intentionally an evaluation/reference API, not a tenant-isolated customer control plane. Health and source metadata are public; assessment, compilation, and evidence routes require `X-Continuity-API-Key`. Run `CONTINUITYOS_API_KEY=... bash scripts/smoke_live.sh https://aiautomatedsystems.ca/continuityos` to verify authenticated integrity, or omit the key to verify that protected evidence is rejected. Deployment files and rollback notes are in [`deploy/README.md`](deploy/README.md).

## API

### Assess a corridor

`POST /v1/assess` (requires `X-Continuity-API-Key`)

```json
{
  "corridor_id": "northwest-passage-west",
  "observations": []
}
```

Observations must pass the registry rules in `src/continuityos/sources/registry.py`.

### Analyze cyber-physical blast radius

`POST /v1/graph/analyze?failed_nodes=shared-idp&failed_nodes=satcom-a` (requires `X-Continuity-API-Key`)

Body: a `DependencyGraph` such as `examples/arctic_dependency_graph.yaml` converted to JSON.

### Compile a continuity plan

`POST /v1/compile` (requires `X-Continuity-API-Key`)

The compiler is exact for up to 24 actions by default. It rejects larger unbounded plans rather than silently using a heuristic. A production OR-Tools adapter can implement the same evidence contract for larger action sets.

### Operator telemetry authentication

Clients serialize payload JSON with sorted keys, then sign:

```text
HMAC-SHA256(secret, "<unix_timestamp>.<canonical_json_body>")
```

Headers:

```text
X-Continuity-Timestamp: 1784820000
X-Continuity-Signature: sha256=<hex digest>
```

Production requires a secret of at least 32 characters and Ed25519 evidence keys.

### Multivariate continuity analysis

`POST /v1/analysis/regression` accepts a time-aligned, provenance-bearing dataset of normalized multidisciplinary indicators and returns a temporal-holdout ridge-regression result. It is associational exploratory analysis only—not causal inference, intelligence, operational forecasting, or autonomous control. The endpoint requires the API key and writes the model result to the evidence ledger. See [`docs/MULTIVARIATE_ANALYSIS.md`](docs/MULTIVARIATE_ANALYSIS.md).

### National-security posture

The project is positioned as a Canadian-oriented, unclassified continuity evidence and decision-support layer for critical infrastructure, Arctic logistics, maritime corridors, communications resilience, and supply-chain dependencies. It does not claim NORAD/NATO/Five Eyes endorsement, classified readiness, government procurement, or authority over operational systems. See [`docs/NATIONAL_SECURITY_POSTURE.md`](docs/NATIONAL_SECURITY_POSTURE.md), [`docs/CONTRACT_AND_SYSTEM_POSITIONING_2026.md`](docs/CONTRACT_AND_SYSTEM_POSITIONING_2026.md), [`docs/CANADIAN_PROCUREMENT_RESEARCH_2026.md`](docs/CANADIAN_PROCUREMENT_RESEARCH_2026.md), and [`docs/PLATFORM_POSITIONING_RESEARCH_2026.md`](docs/PLATFORM_POSITIONING_RESEARCH_2026.md).
### Operational endpoints

- `GET /livez` is a cheap process liveness check for a supervisor.
- `GET /readyz` checks runtime evidence storage, production key files, and ledger integrity.
- `GET /healthz` preserves the public compatibility response and includes readiness/integrity details.
- `GET /metrics` exposes minimal Prometheus-compatible counters; place it behind the existing private ingress or firewall in a customer deployment.
- `GET /v1/public-data/sources` requires the API key and lists the allow-listed public source manifests, freshness policy, parser, and key requirement.
- `POST /v1/public-data/snapshots` requires the API key and fetches only an allow-listed source; it returns HTTP 503 when outbound HTTP is disabled and stores successful responses as immutable content-addressed snapshots.
- `POST /v1/public-data/indicators` requires the API key and serves normalized ECCC GeoMet alert indicators or DFO IWLS water-level observations. ECCC returns alert-event values with expiration/geometry/confidence flags; DFO returns station/data snapshot IDs, source-native units, and QC/review flags. It serves cached snapshots when outbound HTTP is disabled and returns HTTP 503 only when the requested evidence is absent.
- `GET /v1/interoperability` requires the API key and returns the machine-readable standards capability manifest. It distinguishes implemented, source-consumer, contract-only, and planned boundaries.
- `POST /v1/integrations/cloudevents` accepts a signed CloudEvents 1.0 envelope for the approved `com.continuityos.operator.observation.v1` type. The event is HMAC-verified, tenant/asset/sequence-validated, idempotent, and written to the evidence ledger; unknown event types are rejected.
- `POST /v1/integrations/cap` accepts protected CAP 1.2 XML metadata, rejects DOCTYPE/ENTITY payloads, preserves alert lifecycle/area fields, and records the normalized alert in the ledger. It does not dispatch or retransmit alerts.
- `scripts/public_data_probe.py --enable-outbound` performs an explicit operator-run source probe; it never runs as a hidden background job.
- `scripts/public_indicator_probe.py --enable-outbound` exercises the ECCC and DFO normalizers against real endpoints and emits sanitized provenance/QC output only.
- `scripts/public_indicator_probe.py --enable-outbound --include-cdd` also parses the official Public Safety Canada CDD XLSX. The CDD is historical aggregated context only; its indicators carry `aggregated_secondary_source` and `not_primary_source` flags.
- `scripts/validate_regression_dataset.py` validates a provenance-bearing JSON dataset before it is submitted to `/v1/analysis/regression`; rows also carry normalization method, quality flags, review state, label definition, and licence declaration.
- `GET /v1/evidence/verify` and `GET /v1/evidence?offset=0&limit=100` require the API key and are bounded/paginated.
- Mutating routes accept `Idempotency-Key`; a same-key same-payload retry returns the original response, while a changed payload returns HTTP 409.
- Operator telemetry requires timestamped HMAC and monotonically increasing tenant/asset sequence numbers; replay returns HTTP 409.
- Every response includes `X-Request-ID`; clients may provide one for correlation.
- Requests larger than `CONTINUITYOS_MAX_REQUEST_BYTES` are rejected before parsing. Protected routes use a process-local rate limit suitable for the single-worker reference service.
- `bash scripts/iac_verify.sh` validates provider-free Terraform, Docker Compose configuration, shell syntax, and the plan-only local deployment. `terraform -chdir=infra/terraform apply -var='apply_local=true'` is an explicit opt-in deployment action.

## Open-source and public data plane

Implemented adapters and boundaries include:

- NOAA@NSIDC Sea Ice Index daily extent CSV
- Environment and Climate Change Canada GeoMet OGC API normalization boundary
- Copernicus Data Space Ecosystem Sentinel-1 STAC metadata search
- ECMWF open-data registry and licensing boundary
- CelesTrak GP JSON for orbital geometry context only
- NGA World Port Index for port geolocation and published characteristics only
- MarineCadastre.gov historical AIS import boundary
- UN Comtrade trade-exposure boundary
- authenticated operator telemetry for live availability, capacity, cyber health, and insurance access
- structured analyst assessments for geopolitical and policy judgments

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md), [`docs/PUBLIC_DATA_CATALOG_2026.md`](docs/PUBLIC_DATA_CATALOG_2026.md), [`docs/PUBLIC_DATA_TERMS_AND_CONTROL_MAP_2026.md`](docs/PUBLIC_DATA_TERMS_AND_CONTROL_MAP_2026.md), [`docs/CUSTOMER_TELEMETRY_AND_LABEL_CONTRACT_2026.md`](docs/CUSTOMER_TELEMETRY_AND_LABEL_CONTRACT_2026.md), [`docs/INTEROPERABILITY_PROFILE_2026.md`](docs/INTEROPERABILITY_PROFILE_2026.md), and [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md).

A release validation against the official NSIDC daily file is recorded in
[`validation/open_data_validation.json`](validation/open_data_validation.json). The derived
Arctic-wide extent anomaly is deliberately marked context-only and cannot lower a live
corridor-risk score. Reproduce it with:

```bash
PYTHONPATH=src python scripts/validate_nsidc_snapshot.py /path/to/N_seaice_extent_daily_v4.0.csv
```

The expanded maritime logistics graph in
[`examples/arctic_maritime_logistics.yaml`](examples/arctic_maritime_logistics.yaml) models
ice-service data, weather, satellite diversity, escort scheduling, an icebreaker, an
ice-capable carrier, fuel, port cyber dependencies, inventory, and a dependent community.

## Verification

```bash
make verify
```

Runs:

- Ruff linting
- mypy strict type checking
- pytest
- coverage report
- package build
- demo execution
- evidence-ledger verification path

For a repeatable operator setup, run `bash scripts/install.sh`. For day-two operations use `bash scripts/status.sh`, `bash scripts/backup_data.sh`, and the restore command documented in [`deploy/README.md`](deploy/README.md).

## Repository map

```text
src/continuityos/
  compiler.py       deterministic continuity compiler
  config.py         fail-closed production settings
  domain.py         validated domain contracts
  evidence.py       signed append-only evidence chain
  fusion.py         source-qualified risk fusion
  graph.py          cyber-physical blast-radius engine
  ingest.py         cache-first open-source ingestion
  service.py        FastAPI application
  telemetry.py      authenticated operator observations
  sources/          adapters, cache, policy, registry

docs/
  ARCHITECTURE.md
  DATA_SOURCES.md
  NOVELTY.md
  THREAT_MODEL.md
  DEPLOYMENT.md
  PRIOR_ART.md

examples/
  arctic_dependency_graph.yaml
  arctic_maritime_logistics.yaml

validation/
  open_data_validation.json

RELEASE_REPORT.md
```

## Production limitations

This is a reference implementation. A production deployment still requires:

- customer-specific identity, authorization, tenant isolation, and data-retention controls;
- Postgres or another transactional evidence index around the immutable ledger;
- enterprise key management or HSM-backed Ed25519 signing;
- schema versioning and migration governance;
- validated domain transforms for local ice concentration, weather, AIS, port capacity, and inventory;
- security accreditation, red-team testing, disaster recovery, and operational runbooks;
- legal review of data licences, export controls, privacy, and procurement requirements;
- model calibration against real decision and outcome data.

No claim of patentability is made. See [`docs/NOVELTY.md`](docs/NOVELTY.md), [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md), and [`RELEASE_REPORT.md`](RELEASE_REPORT.md).
