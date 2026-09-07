# Aegis ContinuityOS — Comprehensive Threat Model (STRIDE)

This document formalizes the security architecture, adversary models, threat surfaces, and defensive countermeasures of the **ContinuityOS** Resilience-as-Code platform for v1.0.

---

## 1. System Architecture & Trust Boundaries

```text
[ UNTRUSTED EXTERNAL TELEMETRY ]  --> [ AIS / Weather / SAR / Satellite Feeds ]
                                                  │
                                                  ▼
                                      ┌──────────────────────┐
                                      │  Sources & Adapters  │  (Input Sanitization & Decay)
                                      └──────────┬───────────┘
                                                 │
═════════════════════════════════════════════════╪══════════════════════════════════════
TRUST BOUNDARY 1: INGESTION                      │ Normalized Observation
═════════════════════════════════════════════════╪══════════════════════════════════════
                                                 ▼
[ DECLARATIVE POLICY & NETWORK ] ───► ┌──────────────────────┐ ◄─── [ OPERATOR OVERRIDES ]
                                      │   Continuity Engine  │
                                      │  (Closure, Policy,   │
                                      │   Trust, Reconcile)  │
                                      └──────────┬───────────┘
                                                 │
═════════════════════════════════════════════════╪══════════════════════════════════════
TRUST BOUNDARY 2: IMMUTABLE AUDIT & EXECUTION    │
═════════════════════════════════════════════════╪══════════════════════════════════════
                                                 ▼
                                      ┌──────────────────────┐
                                      │   Evidence Ledger    │  (SHA-256 + Ed25519)
                                      │  (Zero-Trust Audit)  │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      [ ADVISORY REMEDIATION ]
                                      (Human-in-the-Loop)
```

---

## 2. Adversary Taxonomy & Threat Scenarios

| Threat Actor | Motivation | Attack Vectors |
| :--- | :--- | :--- |
| **Sophisticated Nation-State (EW/Cyber)** | Disruption of maritime logistics, GNSS spoofing | AIS kinematic spoofing, false telemetry injection, LEO jamming |
| **Commercial Competitor / Insider** | Market manipulation, route delay coverup | Forged bills of lading, false port throughput reports |
| **Hostile Network Intermediary** | Tampering with air-gapped transit packages | Man-in-the-Middle (MitM) alterations, hash collision attacks |
| **Accidental / Environmental Failure** | Unintentional telemetry dropouts | Geomagnetic solar storms, fiber cuts, underwriter withdrawal |

---

## 3. STRIDE Threat Analysis & Countermeasures

### 3.1 Spoofing Identity & Source Telemetry
- **Threat**: Adversary transmits falsified AIS vessel positions or synthetic open navigation status over a closed chokepoint.
- **Countermeasure**: Multi-dimensional `DependencyTrust` engine with multi-factor risk fusion. Observations require independent source qualification (minimum 2 independent observation platforms). High-trust authoritative feeds override single commercial streams.

### 3.2 Tampering with Evidence & State History
- **Threat**: Malicious actor alters historical disruption logs or falsifies compliance status to avoid regulatory fines or insurance surcharges.
- **Countermeasure**: Append-only `EvidenceLedger` protected by cryptographic SHA-256 block hash chaining and Ed25519 digital signatures. Any retrospective modification breaks the cryptographic hash chain and fails `continuity verify-ledger`.

### 3.3 Repudiation of Operational Directives
- **Threat**: Operators or providers dispute having received disruption alerts or issued emergency route diversions.
- **Countermeasure**: Cryptographically signed immutable ledger entries record every observation, policy evaluation, and advisory remediation recommendation with millisecond UTC timestamps and operator keys.

### 3.4 Information Disclosure & Enclave Leakage
- **Threat**: Sensitive defense prime supply routes or critical national stockpile levels leak across enclaves or over unencrypted internet connections.
- **Countermeasure**: 
  - Zero cloud phone-home mechanisms.
  - Cross-domain sanitize filtering (`continuity cross-domain-filter`) strips classified compartment metadata when transitioning from Secret to Unclassified enclaves.
  - Post-Quantum ML-KEM sealed intel envelopes protect sensitive payloads.

### 3.5 Denial of Service (Resource Exhaustion)
- **Threat**: Adversary provides malicious recursive YAML files, cycles in dependency graphs, or astronomical scenario durations to exhaust CPU/memory.
- **Countermeasure**:
  - Safe YAML parsing with strict recursion depth limits (max 50) and file size caps (10MB).
  - Graph cycle detection algorithms (`detect_cycles()`) detect and abort infinite traversal loops.
  - Pydantic v2 schemas enforce bounded constraints on integer durations and array lengths.

### 3.6 Elevation of Privilege & Autonomous Dispatch
- **Threat**: Software autonomously routes ships into hostile waters or dispatches physical assets without human commander authorization.
- **Countermeasure**: Non-negotiable architectural boundary: All plan compilations, substitution options, and reconciliations are strictly **advisory**. Automated kinetic dispatch is architecturally prohibited in the open-core runtime.

---

## 4. Zero-Cloud & Air-Gapped Verification

ContinuityOS v1.0 guarantees:
1. **Network Independence**: The entire test suite, demo commands, and CLI operations execute with network interfaces disabled.
2. **Local Mock Providers**: All external data sources (NOAA, Sentinel, AIS, SATCOM) have offline mock implementations (`MockProvider`) for SCIF and air-gap deployments.
3. **No Dynamic Code Execution**: The DSL is purely declarative YAML; no arbitrary Python `exec()`, `eval()`, or untrusted WASM execution is permitted.
