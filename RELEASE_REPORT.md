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
10. FastAPI and CLI interfaces

## Verification completed in the build environment

- Package installed from source with no dependency resolution.
- Python bytecode compilation completed successfully.
- Test suite: **29 passed**.
- Statement coverage: **86.44%**.
- Coverage release gate: **85% passed**.
- Demonstration scenario completed and produced valid JSON.
- Ed25519 evidence key generation completed.
- Signed evidence creation and verification completed.
- Wheel package built successfully and installed into an isolated target.
- Installed-wheel FastAPI `/healthz` smoke test passed.
- Official NSIDC daily snapshot parser validation passed against data through 2026-07-22.
- Expanded 15-node Arctic maritime logistics graph validated and analyzed.

## Release artifact

- Wheel: `continuityos_reference-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `e9f859ddfd7967e15d773f6ad17ee328aa0e14e1a61b777bd7fad6cf6925fcf0`

## Verification not completed locally

- Docker/Podman was not present, so the container image was not built or smoke-tested locally.
- Ruff and mypy were not available in the environment.
- The configured package registry returned HTTP 503 while resolving transitive packages, so a complete `uv.lock` could not be generated.

These items are exposed rather than represented as passed. CI and `scripts/verify_release.sh` contain the intended lint, strict type-check, test, build, demo, and ledger-verification path for a connected trusted registry.

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
