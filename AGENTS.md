# ContinuityOS — Agent Engineering Guide & System Specifications

Welcome to **ContinuityOS**, the open-core **Continuity-as-Code / Resilience-as-Code** engine for critical trade corridors and physical-digital supply networks.

This document serves as the authoritative guide for AI coding agents and human contributors working on this repository.

---

## 1. Product Thesis

Traditional Infrastructure-as-Code answers:
> *Is my infrastructure configured as intended?*

Kubernetes answers:
> *Is my application operating in its desired state?*

**ContinuityOS answers:**
> *Will my supply chain, logistics network, or critical mission corridor function through degradation, denial, and cascade failure — and what exact, explainable, bounded actions restore continuity?*

Resilience is **not binary** (OPEN vs. CLOSED). Infrastructure can remain physically open while becoming operationally or commercially unusable:
- **`OPEN_BUT_UNINSURABLE`** — route physically clear, but Lloyd's / war-risk underwriters withdraw coverage.
- **`OPEN_BUT_NO_CARRIER_CAPACITY`** — ports open, but container carriers divert vessels away.
- **`OPEN_BUT_NAVIGATION_UNTRUSTED`** — waterway navigable, but GNSS spoofing / PNT loss makes transit unsafe.
- **`OPEN_BUT_COMMUNICATIONS_DEGRADED`** — polar corridor open, but solar flares / geomagnetic blackouts disable SATCOM.
- **`RECOVERY_BACKLOGGED`** — route reopened, but port congestion and vessel repositioning create weeks of recovery lag ($T0 \to T5$).

---

## 2. Defensive-Only Safety Boundary

ContinuityOS is strictly engineered for **defensive resilience planning, business continuity, critical infrastructure protection, disaster recovery, and logistics assurance**.

- **NEVER** implement offensive cyber operations, adversary targeting, weapon payload routing, or interdiction features.
- **NEVER** implement autonomous dispatch or automatic execution of consequential actions.
- **ALWAYS** enforce the human approval boundary: plan compilation, remediation options, and recovery timelines are strictly **advisory**.

---

## 3. Architecture Overview & Core Modules

```
src/continuityos/
├── domain.py          # Core domain models, 12-state CorridorState enum, metrics, observations
├── dsl.py             # Declarative YAML DSL (apiVersion: continuity.io/v1) for SupplyNetwork, Policy, Trust, Scenario
├── schemas.py         # JSON Schema export and validation utilities
├── trust.py           # Multi-dimensional DependencyTrust engine (9 dimensions, 3 aggregation strategies)
├── graph.py           # DependencyGraph engine with cycle detection, path finding, and blast-radius modeling
├── fusion.py          # Multi-factor source-qualified risk fusion engine with freshness decay
├── closure.py         # Functional Closure engine (physical, operational, commercial, trust layer decomposition)
├── policy.py          # Policy-as-Code evaluation engine (minimum providers, reserves, routes, continuity, trust)
├── reconcile.py       # Kubernetes/Terraform-style desired vs. actual state reconciliation
├── scenario.py        # Correlated failure scenario simulation engine (defensive cascade propagation)
├── inventory.py       # Time-series inventory depletion simulation with day-by-day threshold tracking
├── recovery.py        # Recovery lag timeline engine modeling T0 (incident) through T5 (full restoration)
├── remediation.py     # Advisory remediation option generator with confidence and cost estimates
├── compiler.py        # Deterministic bounded exact solver for mitigation plan generation
├── evidence.py        # Append-only SHA-256 evidence ledger with Ed25519 cryptographic signatures
├── crypto.py          # Post-Quantum hybrid envelopes (ML-DSA), Merkle inclusion proofs & sealed intel (ML-KEM)
├── threat.py          # Cyber-physical threat anomaly engine (GNSS EW spoofing, Port SCADA, AIS kinematics)
├── intelligence.py    # Machine learning Bayesian cascade forecaster, stream anomaly detector & XAI Shapley explainer
├── exchange.py        # Interoperability export (GeoJSON, GeoPackage, NDJSON)
├── sovereign.py       # Sovereign security, security labeling, air-gap SCIF audit, and cross-domain guards
├── readiness.py       # Defense Readiness Reporting System (DRRS) & NATO C-Level capability rating
├── cop.py             # MIL-STD-2525D / NATO APP-6D Common Operating Picture symbology exporter
├── cli.py             # Unified CLI (continuity / continuityos) with 23 commands
├── service.py         # FastAPI sovereign REST service with rate limiting, idempotency, and audit trails
├── providers/         # Provider SDK and offline MockProvider implementation
└── sources/           # Public authoritative data adapters, caching, and policy enforcement
```

---

## 4. Declarative DSL Specification (`continuity.io/v1`)

ContinuityOS resources are declared as YAML documents:

### Resource Kinds
- `SupplyNetwork`: Declares desired redundancy, inventory reserves, failure tolerance, and recovery constraints.
- `ContinuityPolicy`: Declares resilience rules evaluated against observed supply network state.
- `DependencyTrust`: Declares multi-dimensional trust ratings (0.0–1.0) across physical, cyber, legal, commercial, insurance, communications, navigation, and operator confidence.
- `Scenario`: Declares correlated disruption events for defensive simulation.

### Validation
Validate any spec via the CLI:
```bash
continuity validate examples/arctic/network.yaml
```

---

## 5. CLI Command Reference

The `continuity` (or `continuityos`) CLI provides 23 subcommands:

| Command | Purpose |
|---|---|
| `init <dir>` | Scaffold a new Continuity-as-Code directory with `network.yaml` and `policy.yaml` |
| `validate <file>` | Validate declarative YAML files against JSON Schema rules |
| `graph <file>` | Analyze dependency graph, detect cycles, find alternate paths, calculate blast radius |
| `observe [--mock]` | Ingest real observations or generate synthetic observations with `MockProvider` |
| `assess <file>` | Run multi-factor risk fusion on corridor observations |
| `compile / plan` | Compile bounded mitigation plans using the deterministic solver |
| `reconcile / drift` | Reconcile declared resilience policy against actual observed state |
| `simulate` | Simulate correlated multi-event failures against a dependency graph |
| `inventory <file>` | Simulate day-by-day strategic inventory depletion |
| `recovery <file>` | Model T0-T5 recovery lag timeline and identify critical path bottlenecks |
| `remediate <file>` | Generate advisory remediation options from reconciliation findings |
| `explain <file>` | Explain functional closure root causes across the 4 decomposition layers |
| `doctor` | Run comprehensive system diagnostics (Python, Ed25519, schemas, offline mock) |
| `verify-ledger` | Cryptographically verify evidence ledger hash chains and Ed25519 signatures |
| `generate-evidence-keys` | Generate new Ed25519 keypairs for evidence signing |
| `sovereign-audit` | Audit air-gapped readiness, cryptographic key isolation, and SCIF compliance |
| `readiness <file>` | Evaluate Defense Readiness (DRRS) & NATO C-Level capability ratings |
| `export-cop <file>` | Export corridor operational status as Mil-Std-2525D / NATO APP-6D GeoJSON COP |
| `cross-domain-filter` | Filter and sanitize payloads across classification and security enclaves |
| `threat-scan <file>` | Scan telemetry for cyber-physical threats (GNSS EW spoofing, SCADA floods, AIS kinematics) |
| `ai-forecast --graph ...` | Bayesian cascade failure probability forecasting across supply graph |
| `xai-explain <file>` | Explain corridor risk breakdown using Shapley factor attribution (Explainable AI) |
| `merkle-proof <ledger>` | Generate and verify zero-knowledge Merkle inclusion proofs for ledger records |

---

## 6. Code Standards & Testing Invariants

- **Language & Runtime**: Python 3.12+ with strict typing via `mypy`.
- **Platform Portability**: All file operations, locking, and path handling must be 100% cross-platform (Windows `msvcrt`, Unix `fcntl`).
- **Code Style**: Formatted and linted via `ruff` with 100-character line length.
- **Coverage**: Test suite must maintain $\ge 85\%$ test coverage across the codebase.
- **Determinism**: Plan compilation, scenario simulation, and inventory models must produce bit-for-bit deterministic results for identical inputs.

### Verification Commands
```bash
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=continuityos --cov-fail-under=85
```
