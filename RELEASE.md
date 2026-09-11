# ContinuityOS Release Engineering Guide (v1.0)

This document establishes the release procedures, semantic versioning gates, and supply-chain integrity standards for ContinuityOS.

---

## 1. Semantic Versioning & Release Cadence

ContinuityOS adheres strictly to [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR (`v1.0.0`)**: Incompatible changes to declarative DSL schemas (`continuity.io/v1`), domain models, or CLI breaking flags.
- **MINOR (`v1.1.0`)**: Backwards-compatible feature additions (e.g. new provider adapters, new trust dimensions, enhanced solver capabilities).
- **PATCH (`v1.0.1`)**: Backwards-compatible security patches, bug fixes, or performance optimizations.

---

## 2. Release-Candidate Verification Gate

Before any release tag is created, the candidate commit must satisfy all 14 gates:

| Gate | Verification Command | Required Outcome |
| :--- | :--- | :--- |
| **1. Linting** | `uv run ruff check .` | 0 errors |
| **2. Formatting** | `uv run ruff format --check .` | All files already formatted |
| **3. Type Safety** | `uv run mypy src` | Success: no issues found (62 modules) |
| **4. Unit Tests** | `uv run pytest` | 486 passed, 0 failed |
| **5. Code Coverage** | `uv run pytest --cov=continuityos --cov-fail-under=85` | $\ge 85\%$ (Current: **94.09%**) |
| **6. Core Invariants** | `uv run pytest tests/test_v1_core_invariants.py` | 10/10 passed |
| **7. Golden Scenarios** | `uv run pytest tests/test_golden_scenarios.py` | 10/10 passed |
| **8. Benchmarks** | `uv run pytest tests/test_benchmark_v1.py` | Sub-second execution (<0.5s) |
| **9. Threat Scan** | `uv run python scripts/threat_stress_harness.py` | 0 vulnerabilities detected |
| **10. Air-Gap Audit** | `uv run continuity sovereign-audit` | Cryptographic integrity verified |
| **11. Sovereign Compliance** | `uv run continuity verify-compliance --profile all` | All profiles (ITSG-33, PBMM, SCIF) SATISFIED |
| **12. Standalone Web Console** | `cd ui && npm run build` | 24/24 static pages prerendered cleanly |
| **13. Master 100 Roadmap** | `ROADMAP-100.md` | 100/100 items verified and executed |
| **14. Release Build** | `uv build && uv run python scripts/generate_release_artifacts.py` | Distributions, SBOM & SHA256SUMS generated |

---

## 3. Release Artifact Generation

To build signed release artifacts:

```bash
# 1. Build source distribution and binary wheel
uv build

# 2. Generate SHA-256 checksums and SPDX 2.3 SBOM
uv run python scripts/generate_release_artifacts.py
```

Generated artifacts located in `dist/`:
- `continuityos-1.0.0.tar.gz` (Source distribution)
- `continuityos-1.0.0-py3-none-any.whl` (Python binary wheel)
- `SHA256SUMS.txt` (SHA-256 digests)
- `continuityos-1.0.0.spdx.json` (Machine-readable SPDX 2.3 Software Bill of Materials)

---

## 4. Verifying Release Integrity

To verify artifact integrity after downloading:

```bash
# Verify checksums
sha256sum -c dist/SHA256SUMS.txt

# Inspect SBOM
cat dist/continuityos-1.0.0.spdx.json | jq .name
```
