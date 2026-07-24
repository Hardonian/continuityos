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
- Test suite: **54 passed**.
- Statement coverage: **85.51%**.
- Coverage release gate: **85% passed**.
- Demonstration scenario completed and produced valid JSON.
- Ed25519 evidence key generation completed.
- Signed evidence creation and verification completed.
- Wheel package built successfully and installed into an isolated target.
- Installed-wheel FastAPI `/healthz` smoke test passed.
- Local `make verify` passed (Ruff, format, mypy, coverage, build, demo, evidence smoke).
- Docker image build passed; Docker Compose health and protected-route smoke passed with non-root runtime and initialized key volume.
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
- Standards-backed interoperability manifest added at `/v1/interoperability` and verified locally/publicly with anonymous HTTP 401 and authenticated HTTP 200. It reports seven capabilities with explicit implemented/source-consumer/contract-only/planned status; it does not claim conformance certification.
- Authoritative interoperability references recorded for CloudEvents 1.0, OGC API Features 1.0.1, OGC SensorThings 1.1, STAC API 1.0.0, CAP 1.2, and OTLP/HTTP.
- Exact runtime deployment verification after the final service restart: systemd active, `MainPID=2843702`, `ExecMainStatus=0`, local `127.0.0.1:8082` and public Caddy/Cloudflare route success for authenticated interoperability manifest and CDD indicators.
- GitHub Actions run pending for the final interoperability commit.

## Release artifact

- Wheel: `continuityos_reference-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `db1f02966a5bafb144e50c856862112e3c4f841a71bb365efb89f861a1b86d80`
- Source distribution SHA-256: `c39cd123500dcaa88648bbf0217876075dc5915b9827ae5b2c27204c248fa280`
- Docker image digest: `sha256:b1d2ee46e876d7bdc64d91e269388fc375622881fa3f31c14712729979d7845a`

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
