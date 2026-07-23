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
cp .env.example .env
docker compose build
docker compose up
curl http://127.0.0.1:8080/healthz
```

The container has no outbound data access unless `CONTINUITYOS_OUTBOUND_HTTP_ENABLED=true` is explicitly set.

## Live reference deployment

The current EPYC-hosted reference surface is available at `https://aiautomatedsystems.ca/continuityos/`.
It is intentionally an evaluation/reference API, not a tenant-isolated customer control plane. Run `bash scripts/smoke_live.sh https://aiautomatedsystems.ca/continuityos` to verify health, source registry, and evidence integrity. Deployment files and rollback notes are in [`deploy/README.md`](deploy/README.md).

## API

### Assess a corridor

`POST /v1/assess`

```json
{
  "corridor_id": "northwest-passage-west",
  "observations": []
}
```

Observations must pass the registry rules in `src/continuityos/sources/registry.py`.

### Analyze cyber-physical blast radius

`POST /v1/graph/analyze?failed_nodes=shared-idp&failed_nodes=satcom-a`

Body: a `DependencyGraph` such as `examples/arctic_dependency_graph.yaml` converted to JSON.

### Compile a continuity plan

`POST /v1/compile`

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

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) and [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md).

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
