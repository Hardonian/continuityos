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

## Verification completed in the build environment

- Package installed from source with pinned dependency resolution.
- Python bytecode compilation completed successfully.
- Test suite: **35 passed**.
- Statement coverage: **86.76%**.
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
- `/livez`, `/readyz`, and `/healthz` passed locally and through the public route.
- Idempotency replay and payload-conflict tests passed; telemetry sequence replay is rejected with HTTP 409.
- Isolated fresh Compose deployment passed production `/readyz` and `/livez` with generated development secrets.
- Local latency smoke: `/livez` p50 1.266 ms/p99 2.152 ms; `/readyz` p50 1.354 ms/p99 1.694 ms; `/healthz` p50 1.292 ms/p99 1.639 ms.
- Runtime dependency versions verified after restart: FastAPI 0.139.2, Starlette 1.3.1, cryptography 49.0.0.
- Official NSIDC daily snapshot parser validation passed against data through 2026-07-22.
- Expanded 15-node Arctic maritime logistics graph validated and analyzed.

## Release artifact

- Wheel: `continuityos_reference-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `970f25e85e35b90869b5443c1e93ae4adb1c4e3593e2958de2205ec1b1aa56e9`
- Source distribution SHA-256: `ba311e1891bd5a7fced973df5f1903b9591332bef38451ed1251452b38c39636`

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
