# ContinuityOS Reference Release Report

## Release

- Package: `continuityos-reference`
- Version: `0.1.0`
- Runtime: Python 3.12+
- Scope: defensive cyber-physical continuity decision support

## Implemented control chain

1. Source registry and assertion allow-lists
2. Immutable content-addressed snapshot cache
3. Open-source data adapters and normalization boundaries
4. Deterministic risk, confidence, freshness, and missing-data fusion
5. Cyber-physical dependency and blast-radius analysis
6. Bounded exact continuity-plan compiler
7. Human-approval flags for consequential actions
8. HMAC-authenticated operator telemetry
9. Hash-chained and optionally Ed25519-signed evidence records
10. API-key protected operator routes, request limits, request IDs, metrics, idempotency, replay protection, and paginated evidence
11. FastAPI and CLI interfaces
12. Source-specific ECCC GeoMet alert and DFO IWLS water-level normalizers with quality/provenance preservation
13. Protected normalized-indicator route operating from immutable cached snapshots while outbound HTTP remains disabled
14. Regression rows carrying normalization method, quality flags, review state, label definition, and licence declaration

## Verification completed in the build environment

- Package installed from source with pinned dependency resolution.
- Python bytecode compilation completed successfully.
- Test suite: **59 passed**.
- Statement coverage: **86.70%**.
- Coverage release gate: **85% passed**.
- Demonstration scenario completed and produced valid JSON.
- Ed25519 evidence key generation completed.
- Signed evidence creation and verification completed.
- Wheel package built successfully and installed into an isolated target.
- Installed-wheel FastAPI `/healthz` smoke test passed.
- Local `make verify` passed (Ruff, format, mypy, coverage, build, demo, evidence smoke).
- Docker image build passed; disposable Docker health and protected GeoPackage export smoke passed with non-root runtime and ephemeral read-only Ed25519 key volume.
- Backup/checksum and disposable restore drill passed.
- Gitleaks scan passed with no leaks found.
- Public unauthenticated evidence access returned HTTP 401; authenticated live smoke passed.
- `/livez`, `/readyz`, and `/healthz` passed locally and through the public route.
- Idempotency replay and payload-conflict tests passed; telemetry sequence replay is rejected with HTTP 409.
- Isolated fresh Compose deployment passed production `/readyz` and `/livez` with generated development secrets.
- Local latency smoke: `/livez` p50 1.266 ms/p99 2.152 ms; `/readyz` p50 1.354 ms/p99 1.694 ms; `/healthz` p50 1.292 ms/p99 1.639 ms.
- Runtime dependency versions verified after restart: FastAPI 0.139.2, Starlette 1.3.1, cryptography 49.0.0.
- Official NSIDC daily snapshot parser validation passed against data through 2026-07-22.
- Expanded 15-node Arctic maritime logistics graph validated and analyzed.
- Governed public-data snapshot plane added with protected source listing and fail-closed fetch routes.
- Real public-source probe succeeded with HTTP 200 for ECCC GeoMet, Statistics Canada WDS, Copernicus CDSE STAC, USGS Water, NOAA SWPC, GDACS, OpenAlex, and GDELT; responses were stored or reused as content-addressed snapshots with SHA-256 provenance.
- Probe evidence included snapshot record counts: ECCC 100, Statistics Canada 8,212, Copernicus 10, USGS 35, NOAA SWPC 1, GDACS 99, OpenAlex 10, and GDELT 1.
- Public Safety Canada CDD XLSX was fetched and schema-inspected, then parsed from an immutable imported snapshot after a subsequent automated portal download returned HTTP 403. The snapshot contains 1,489 historical event rows and produced 6,250 normalized indicators spanning 1900-01-09 through 2022-12-22; every CDD indicator is flagged `aggregated_secondary_source` and `not_primary_source`.
- CDD cached indicator route smoke passed locally and through the public proxy: unauthenticated HTTP 401, authenticated HTTP 200, 6,250 indicators, snapshot `canadian-disaster-database-1321a40003599b690e89`.
- Authoritative provider terms were captured in `docs/PUBLIC_DATA_TERMS_AND_CONTROL_MAP_2026.md`; customer telemetry and labelled-outcome intake requirements were captured in `docs/CUSTOMER_TELEMETRY_AND_LABEL_CONTRACT_2026.md`.
- ReliefWeb correctly failed closed because a registered application name was not configured; NASA FIRMS correctly requires a protected MAP_KEY.
- Live public deployment after commit `1f8d7a8`: `/livez=200`, `/readyz=200`, `/healthz=200`; protected public-data listing returned 200, unauthenticated listing returned 401, and outbound-disabled fetch returned 503.
- Live regression smoke returned 200 for an explicitly synthetic, provenance-shaped 8-row dataset; same-key replay returned 200 with byte-identical response.
- Real normalized-indicator probe completed against ECCC GeoMet and DFO IWLS. ECCC returned 100 alert indicators across alert classes `aqw`, `ehw`, and `stw`; DFO returned 2 current observations from Québec station `03057` Saint-Joseph-de-la-Rive at values `2.115` and `2.555` metres relative to the station product datum.
- DFO station and data snapshots carried separate immutable IDs; source-native QC code `1` and `not_reviewed` status were preserved rather than promoted to a clean-data claim.
- Cached production-route smoke passed with outbound HTTP disabled: local and public `/v1/public-data/indicators` returned HTTP 200 for ECCC and DFO, unauthenticated access returned HTTP 401, and responses contained snapshot IDs and normalized observations.
- Regression governance smoke passed: normalization methods, quality flags, review states, label definition, and licence declaration are returned in the result limitations/metadata.
- Standards-backed interoperability manifest added at `/v1/interoperability` and verified locally/publicly with anonymous HTTP 401 and authenticated HTTP 200. It reports eleven capabilities with explicit implemented/source-consumer/contract-only/planned status; it does not claim conformance certification.
- Authoritative interoperability references recorded for CloudEvents 1.0, OGC API Features 1.0.1, OGC SensorThings 1.1, STAC API 1.0.0, CAP 1.2, and OTLP/HTTP.
- Signed CloudEvents 1.0 observation ingress is implemented at `/v1/integrations/cloudevents` with one approved event type, HMAC verification, event-ID idempotency, replay protection, and ledger recording.
- Protected CAP 1.2 XML ingress is implemented at `/v1/integrations/cap` with bounded payloads, DOCTYPE/ENTITY rejection, lifecycle/area preservation, API-key auth, idempotency, and ledger recording. It does not dispatch or retransmit alerts.
- The protected `/v1/decision-packets` orchestration surface is implemented: one idempotent bounded request produces assessment, dependency impact, deterministic mitigation planning, evidence manifest, approval state, and a human-action boundary; it records component and packet evidence but executes no action.
- The protected `/v1/strategic/analyze` surface is implemented: freshness/confidence-weighted multivariate heatmaps, explainable ranked alerts, human-gated coordination recommendations, and optional provenance-bearing temporal-holdout regression; predictive status and limitations remain explicit.
- Protected GeoJSON, GeoPackage, deterministic NDJSON, and metadata-only STAC catalog exports are implemented for bounded evidence snapshots. The GeoPackage live smoke returned a valid SQLite GeoPackage with seven evidence rows; all new export routes returned anonymous HTTP 401 and authenticated HTTP 200.
- IaC policy checks now fail closed on public binds, privileged workloads, host networking, and unignored Terraform state; `scripts/iac_verify.sh` reports `iac=valid`, `compose=valid`, `shell=valid`, and `policy=valid`.
- Application defense-in-depth headers are now emitted by the API: CSP, frame denial, nosniff, no-referrer, permissions policy, HSTS behind HTTPS forwarding, request IDs, and no-store.
- Non-destructive `make doctor` now verifies repository/runtime ownership, liveness/readiness/health, protected-route rejection, environment-file mode, backup timer, IaC policy, and tracked-secret hygiene.
- The user-level systemd unit now uses a compatible sandbox (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `ProtectHome=read-only`, `LockPersonality`, `RestrictSUIDSGID`, `UMask=0077`, and a data-directory write exception); live restart remained healthy with zero restarts.
- Backup archives now have mode 600, tar validation, and a disposable checksum/path/ledger/state restore verifier; the latest local archive passed verification. Off-host disaster recovery remains open.
- `scripts/drift_check.sh` verifies installed user units match the reviewed repository deployment units, and `docs/OPERATIONS_RUNBOOK_2026.md` records change, incident, rollback, recovery, and approval procedures.
- Go-live posture and host-level MicroK8s exposure blockers are documented in `docs/GO_LIVE_SECURITY_CLOSURE_2026.md`; no host-wide lockdown or national-security accreditation is claimed.
- Provider-free Terraform IaC added under `infra/terraform/`; default behavior is plan-only, with explicit `apply_local=true` required to synchronize user systemd units. Terraform, Compose, shell, and deployment validation are now part of `make verify` and CI.
- Exact runtime deployment verification after the final service restart: systemd active, `MainPID=3443986`, `ExecMainStatus=0`, local `127.0.0.1:8082` and authenticated export/manifest routes passed; anonymous protected routes returned HTTP 401 without writing production data.
- GitHub Actions run `30060053979` for commit `8547d9bc8d069a15a69146931f59287e75537ba8` completed successfully: https://github.com/Hardonian/continuityos/actions/runs/30060053979

## Release artifact

- Wheel: `continuityos_reference-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `2fc3f7f2cbc009ed72d6165539ad370e78cfea3a2f95151a2097b348ce65db07`
- Source distribution SHA-256: `02d889da6b7c720751f2397d53e7e4a9f30ca5470389b6b27a904d064148bffe`
- Docker image digest: `sha256:2bf199bb6c9ad25548572ce4bc430f955a0b9437ad7ea77226ef12b50e3794f6` (`continuityos-reference:0.1.0`; rebuilt after strategic signal implementation; non-root runtime; disposable `/readyz` and `/healthz` smoke passed).

## Verification intentionally not represented as complete

- Multi-tenant identity/RBAC, customer data isolation, and transactional indexed evidence are not implemented by this reference service.
- HSM/KMS signing, off-host encrypted backups, external accreditation, legal review, and customer outcome calibration remain external gates.
- A production restore was not run destructively; only a disposable restore drill was executed.
- GitHub Dependabot now reports zero open alerts. Seven alerts tied to the deleted duplicate manifest were dismissed as inaccurate with an explicit audit comment; the active dependency graph is the patched `pyproject.toml`/`uv.lock` graph.

## Security limitations

This is a reference implementation, not an accredited operational service. It does not include:

- production identity and tenant authorization;
- distributed anti-replay/idempotency storage across replicas; the current locked JSON state is single-deployment only;
- HSM-backed signing;
- database-backed transactional evidence indexing;
- classified-data controls;
- operational port, carrier, insurer, or satellite-provider connectors;
- validated local navigation or ice-route decision models;
- authority to control vessels, ports, OT, drones, or security assets.

## Release decision

**Suitable for architecture evaluation, controlled fictional demonstrations, and a governed pilot data-integration phase. Not approved for operational navigation, autonomous control, classified data, alliance tasking, or production national-security deployment.**
