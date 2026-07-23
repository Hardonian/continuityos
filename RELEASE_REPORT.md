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
10. API-key protected operator routes, request limits, request IDs, metrics, and paginated evidence
11. FastAPI and CLI interfaces

## Verification completed in the build environment

- Package installed from source with pinned dependency resolution.
- Python bytecode compilation completed successfully.
- Test suite: **33 passed**.
- Statement coverage: **87.02%**.
- Coverage release gate: **85% passed**.
- Demonstration scenario completed and produced valid JSON.
- Ed25519 evidence key generation completed.
- Signed evidence creation and verification completed.
- Wheel package built successfully and installed into an isolated target.
- Installed-wheel FastAPI `/healthz` smoke test passed.
- Local `make verify` passed (Ruff, format, mypy, coverage, build, demo, evidence smoke).
- Docker image build passed; Docker Compose health and protected-route smoke passed with non-root runtime and initialized key volume.
- Backup/checksum and disposable restore drill passed.
- Gitleaks scan passed with a narrow type-annotation false-positive allowlist.
- Public unauthenticated evidence access returned HTTP 401; authenticated live smoke passed.
- Official NSIDC daily snapshot parser validation passed against data through 2026-07-22.
- Expanded 15-node Arctic maritime logistics graph validated and analyzed.

## Release artifact

- Wheel: `continuityos_reference-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `79bd36cd3151bf7ef18dc3759804c5ffe17ed617058bb0ec2ab11ad8f030df9b`
- Source distribution SHA-256: `86401d14b3d7114e9f409b01ce1d0c9c03ef81596fb3b6befa53bf38bace83ad`

## Verification intentionally not represented as complete

- Multi-tenant identity/RBAC, customer data isolation, and transactional indexed evidence are not implemented by this reference service.
- HSM/KMS signing, off-host encrypted backups, external accreditation, legal review, and customer outcome calibration remain external gates.
- A production restore was not run destructively; only a disposable restore drill was executed.

## Security limitations

This is a reference implementation, not an accredited operational service. It does not include:

- production identity and tenant authorization;
- durable anti-replay storage across replicas;
- HSM-backed signing;
- database-backed transactional evidence indexing;
- classified-data controls;
- operational port, carrier, insurer, or satellite-provider connectors;
- validated local navigation or ice-route decision models;
- authority to control vessels, ports, OT, drones, or security assets.

## Release decision

**Suitable for architecture evaluation, controlled demonstrations, and a pilot data-integration phase. Not approved for operational navigation, autonomous control, or production national-security deployment.**
