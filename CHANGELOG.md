# Changelog

All notable changes to **ContinuityOS** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-07

### Added
- **10 Core Resilience Invariants**: Strict architectural assertions verified by unit and regression test suites (`tests/test_v1_core_invariants.py`).
- **12-State Operational Model**: Rich operational state taxonomy distinguishing physical status from commercial, insurance, and navigation usability (`domain.py`).
- **Functional Closure Decomposition Engine**: 4-layer evaluation (Physical, Operational, Commercial, Digital Trust) explaining non-physical chokepoint failures (`closure.py`).
- **9-Dimensional Dependency Trust**: Evaluates `physical_availability`, `cyber_integrity`, `legal_availability`, `commercial_availability`, `communications_integrity`, `navigation_integrity`, `insurance_availability`, `operator_confidence`, and `information_confidence` (`trust.py`).
- **Assurance Budgeting Engine (`AssurancePolicy`)**: Quantifies resilience margins, fault tolerances, and verification gates with detailed scorecard generation (`assurance.py`).
- **Provider Independence Analyzer**: Uncovers hidden upstream SPOFs (shared ground stations, power grids, satellite downlinks) to invalidate false redundancy (`independence.py`).
- **Route Substitution Compiler**: Evaluates multi-constraint contingency routes across geographic, vessel class, port handling, inland transit, and inventory arrival deadlines (`substitution.py`).
- **Strategic Inventory & Assured Replenishment**: Day-by-day dynamic burn rate simulation calculating `ASSURED_REPLENISHMENT_DAYS`, warning, critical, and exhaustion thresholds (`inventory.py`).
- **Recovery Lag Engine**: Models the full $T0 \to T5$ restoration timeline, ensuring physical reopening does not prematurely mark networks healthy (`recovery.py`).
- **Correlated Disruption Simulator**: Propagates multi-event cascading failures across complex dependency graphs, computing capacity loss and blast radius (`scenario.py`).
- **Signed Evidence Ledger**: Append-only SHA-256 hash chain with Ed25519 digital signatures, conflict detection, and Merkle inclusion proofs (`evidence.py`, `crypto.py`).
- **Exact Bounded Mitigation Compiler**: Deterministic branch-and-bound solver finding optimal mitigation action subsets under strict budget constraints (`compiler.py`).
- **Unified 26-Command CLI**: Complete open-source developer interface supporting `plan`, `drift`, `assurance`, `substitute`, `simulate`, `explain`, `evidence`, `demo`, and `doctor` (`cli.py`).
- **Zero-Cloud Offline Interactive Demo**: Repeatable 12-step demonstration engine with both Arctic maritime and civilian medical logistics reference implementations (`continuity demo`).
- **Golden Test Suite**: 10 golden test scenarios (A through J) validating all failure modes (`tests/test_golden_scenarios.py`).
- **High-Performance Benchmark Suite**: Validates 10,000 nodes and 50,000 edges cascade propagation in 0.038s, 500 policy evaluations in 0.082s (`tests/test_benchmark_v1.py`).
- **Security & Threat Model Documentation**: Comprehensive STRIDE threat model, air-gapped SCIF hardening guide, and coordinated vulnerability disclosure policy (`SECURITY.md`, `docs/THREAT_MODEL.md`).
- **GTM & Commercialization Collateral**: Product positioning, competitive landscape analysis, pricing strategy, customer pilot roadmap, launch posts, and demo script (`docs/gtm/`).

### Changed
- Normalized package identity to `continuityos` v1.0.0 in `pyproject.toml`.
- Overhauled `README.md` with category framing, 5-minute quickstart, terminal examples, and 6 Mermaid architecture diagrams.
- Upgraded SPOF detection algorithm with fast-path topological pruning, reducing graph traversal latency from 43s to 38ms on 50,000 edges.
- Extended JSON Schemas in `schemas/` to formally validate `AssurancePolicy` and `RouteSubstitution` manifests.

### Security
- Added fail-closed deserialization limits preventing memory exhaustion from malformed YAML/JSON.
- Verified air-gapped cryptographic integrity and Ed25519 signature enforcement under `continuity sovereign-audit`.
- Pinned dependency lockfiles and generated SPDX 2.3 Software Bill of Materials (SBOM).
