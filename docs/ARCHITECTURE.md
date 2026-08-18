# ContinuityOS Architecture

## 1. System Boundary

ContinuityOS is a decision-support and resilience control plane for critical corridors, logistics networks, and cyber-physical supply chains. It observes, compiles, reconciles, and recommends; it does not directly dispatch or operate physical assets.

```text
Authoritative Public Data         Authenticated Telemetry          Provider SDK / Mocks
(Ice, weather, climate, AIS)     (Operator telemetry, OT health)  (Satcom, PNT, port status)
             \                               |                              /
              +------------------------------+-----------------------------+
                                             |
                                   Source Policy Gate
                                             |
                                   Immutable Snapshots
                                             |
                                  Normalized Observations
                                             |
           +---------------------------------+---------------------------------+
           |                                 |                                 |
   Dependency Graph                 Functional Closure               Multi-Dimensional
  (Cycles, SPOFs, Blast)         (Physical, Ops, Comm, Trust)         DependencyTrust
           |                                 |                                 |
           +---------------------------------+---------------------------------+
                                             |
                           Continuity Policy & Reconciliation
                           (Desired vs. Actual State Diffing)
                                             |
                +----------------------------+----------------------------+
                |                            |                            |
       Scenario Simulator           Inventory Depletion          Recovery Lag Engine
     (Correlated Disruption)       (Day-by-Day Forecast)           (T0 -> T5 Timeline)
                |                            |                            |
                +----------------------------+----------------------------+
                                             |
                                 Advisory Remediation &
                                   Continuity Compiler
                                             |
                                    Human Approval Gate
                                             |
                                   Signed Evidence Ledger
                                  (SHA-256 / Ed25519 Chain)
```

---

## 2. Core Resilience Engines

### 2.1 Enriched 12-State Operational Model
Resilience is not binary. The system distinguishes:
- `OPEN` — fully operational and compliant
- `OPEN_DEGRADED` — operational with elevated factor risk
- `OPEN_CAPACITY_CONSTRAINED` — physical throughput bottlenecked
- `OPEN_BUT_UNINSURABLE` — route navigable, but insurance underwriters withdraw coverage
- `OPEN_BUT_NO_CARRIER_CAPACITY` — ports open, but carriers divert vessels
- `OPEN_BUT_NAVIGATION_UNTRUSTED` — GNSS spoofing / PNT loss makes transit unsafe
- `OPEN_BUT_COMMUNICATIONS_DEGRADED` — high-latitude geomagnetic / SATCOM outage
- `OPEN_BUT_SERVICE_DEPENDENT` — reliant on sole-source icebreaker or towing service
- `RECOVERY_BACKLOGGED` — route reopened, but port congestion and repositioning lag
- `FUNCTIONALLY_CLOSED` — multi-layer failure rendering infrastructure unusable
- `PHYSICALLY_CLOSED` — physical destruction or impassable ice barrier
- `UNKNOWN` — unobserved / insufficient data trust

### 2.2 Functional Closure Engine (`closure.py`)
Decomposes infrastructure into four independent layers:
1. **Physical Layer**: Physical accessibility and capacity.
2. **Operational Layer**: Navigation integrity, communications availability, weather safety.
3. **Commercial Layer**: Marine insurance coverage, carrier capacity, economic viability.
4. **Trust Layer**: Data integrity, observation confidence, source diversity.

### 2.3 Dependency Trust Engine (`trust.py`)
Evaluates 9 independent trust dimensions (`physical_availability`, `cyber_integrity`, `legal_availability`, `commercial_availability`, `insurance_availability`, `communications_integrity`, `navigation_integrity`, `operator_confidence`, `information_confidence`) with configurable aggregation (`minimum`, `weighted`, `mean`) and provenance enforcement.

### 2.4 Policy-as-Code & Reconciliation (`policy.py`, `reconcile.py`)
Evaluates declared resilience assertions (`minimum_providers`, `minimum_reserve_days`, `minimum_independent_routes`, `minimum_continuity`, `minimum_trust_score`) against real-world state, producing structured reconciliation statuses: `COMPLIANT`, `DRIFT`, `DEGRADED`, `FAIL`, or `UNKNOWN`.

### 2.5 Correlated Failure Scenarios (`scenario.py`)
Propagates multi-event cyber-physical disruptions through the dependency graph, calculating capacity loss, cascade paths, single points of failure (SPOFs), and policy violations.

### 2.6 Inventory Depletion Engine (`inventory.py`)
Simulates day-by-day depletion of strategic commodities under normal, degraded, and severed replenishment conditions with substitution mitigation.

### 2.7 Recovery Lag Engine (`recovery.py`)
Models the full recovery lifecycle:
- **T0**: Incident occurrence
- **T1**: Physical reopening
- **T2**: Commercial normalization (insurance & carrier return)
- **T3**: Logistics normalization (port backlog clearance & vessel repositioning)
- **T4**: Inventory replenishment (rebuilding reserves)
- **T5**: Full resilience restoration

### 2.8 Advisory Remediation (`remediation.py`)
Generates prioritized, cost-aware remediation options for reconciliation failures. All outputs are strictly advisory and require human approval.

---

## 3. Trust Classes & Fail-Closed Rules

1. **Authoritative Public**: Government and intergovernmental agencies (NOAA, DWD, NSIDC, Copernicus).
2. **Authenticated Operator**: Customer-controlled telemetry authenticated via HMAC-SHA256 or mTLS.
3. **Open Context**: General public context; cannot lower live operational risk or inflate confidence.
4. **Fail-Closed Gate**: Unknown sources, mismatched assertions, or expired observations are rejected at the policy boundary.

---

## 4. Cryptographic Provenance & Evidence

Every assessment, decision packet, and observation is hashed into an append-only SHA-256 hash chain with Ed25519 cryptographic signatures for sovereign auditability.
