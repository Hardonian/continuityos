# CCCS ITSG-33 & Protected B / Medium Integrity / Medium Availability (PBMM) Compliance Matrix

**Platform:** Aegis Continuity / ContinuityOS Sovereign Suite  
**Standard:** Canadian Centre for Cyber Security (CCCS) ITSG-33 / TBS Policy on Government Security (PGS)  
**Security Profile:** Protected B, Medium Integrity, Medium Availability (PBMM)  

---

## 1. Executive Summary

This compliance matrix details how **Aegis Continuity** satisfies the operational, technical, and management security controls prescribed under CCCS ITSG-33 for handling **Protected B** sensitive federal government data, defense logistics information, and critical infrastructure telemetry.

---

## 2. Security Control Domain Mapping

| Family / Control ID | Control Name | PBMM Baseline Requirement | Aegis Continuity Implementation Status | Evidence / Architectural Mechanism |
|:---|:---|:---|:---|:---|
| **AC-2** | Account Management | Role-based lifecycle control for operators and administrators. | **SATISFIED** | Multi-tenant `SovereignTenant` and `SovereignRole` isolation; API keys and JWT claims mapped to clearances. |
| **AC-3** | Access Enforcement | Mandatory clearance and compartment checking before record retrieval. | **SATISFIED** | `SecurityLabel.is_authorized()` strictly enforces clearance levels (`PROTECTED_B`, `SECRET`) and `CANADIAN_EYES_ONLY`. |
| **AC-4** | Information Flow Enforcement | Data diode / cross-domain filtering on high-to-low enclave transfers. | **SATISFIED** | `CrossDomainFilter` prevents classification downgrades and sanitizes internal cryptographic secrets. |
| **AC-17** | Remote Access | Encrypted session transport with mutual authentication. | **SATISFIED** | TLS 1.3 enforced; mTLS supported with x509 client certificates; loopback-only binding behind reverse proxy. |
| **AU-2** | Event Logging | Capture of all administrative, plan compilation, and assessment actions. | **SATISFIED** | JSON-formatted structured access and operational logs emitting timestamps, request IDs, and caller identity. |
| **AU-9** | Protection of Audit Information | Tamper-evident, immutable audit trail. | **SATISFIED** | Append-only SHA-256 evidence ledger with Ed25519 digital signatures and Merkle inclusion proofs. |
| **CA-3** | Information System Interconnections | Explicit validation of external telemetry and data feeds. | **SATISFIED** | Source policy gate in `sources/policy.py` validates allow-listed sources and content-addressed SHA-256 hashes. |
| **CM-2** | Baseline Configuration | Declarative configuration-as-code under version control. | **SATISFIED** | Pure declarative YAML DSL (`continuity.io/v1`) with automated schema validation. |
| **CP-2** | Contingency Plan | Operational continuity under air-gapped or severed network conditions. | **SATISFIED** | `AirGapAuditor` and `MockProvider` enable 100% offline air-gapped SCIF deployments with zero external dependencies. |
| **CP-9** | Information System Backup | Automated daily backup with verified point-in-time recovery. | **SATISFIED** | Automated backup service and reversible disaster recovery drill script (`scripts/restore_data.sh`). |
| **CP-10** | Recovery Plan | Defined RPO (<15m) and RTO (<1h) with multi-region failover. | **SATISFIED** | Sovereign dual-region deployment architecture across AWS Canada Central / West or Azure Canada Central / East. |
| **IA-2** | Identification and Authentication | Multi-factor cryptographic authentication for privileged roles. | **SATISFIED** | Cryptographic Ed25519 signing keys, canonical HMAC telemetry authentication, and API key enforcement. |
| **MP-5** | Media Transport & Data Residency | Physical and logical data residency strictly within Canadian borders. | **SATISFIED** | Cloud deployments restricted exclusively to Canadian sovereign regions (`ca-central-1`, `canadacentral`). |
| **RA-3** | Risk Assessment | Continuous automated risk fusion across cyber and physical domains. | **SATISFIED** | Deterministic `FusionEngine` with freshness decay, missing data penalties, and XAI Shapley factor attribution. |
| **SC-8** | Transmission Confidentiality | TLS 1.3 / Post-Quantum hybrid cipher suites in transit. | **SATISFIED** | Enforced TLS 1.3 cipher suites and post-quantum hybrid encapsulation (ML-KEM / ML-DSA in `crypto.py`). |
| **SC-12** | Cryptographic Key Management | Isolated local key storage or FIPS 140-3 Level 3 CloudHSM. | **SATISFIED** | File permissions strictly mode 0600; zero secret leakage to Git; KMS Customer Managed Key integration. |
| **SC-28** | Protection at Rest | AES-256-GCM / CMK encryption for all persistent state. | **SATISFIED** | Database, snapshots, and evidence ledgers encrypted at rest using customer-owned encryption keys. |
| **SI-4** | Information System Monitoring | Cyber-physical threat anomaly detection and SCADA flood detection. | **SATISFIED** | `threat.py` scans telemetry for GNSS EW spoofing, AIS kinematic jumps, and SCADA control floods. |

---

## 3. Automated PBMM Verification CLI

System administrators can verify continuous PBMM compliance at any time using the automated CLI command:

```bash
continuity pbmm-audit --region ca-central-1 --tls-version 1.3
```

**Expected JSON Output:**
```json
{
  "is_compliant": true,
  "data_residency_region": "ca-central-1",
  "canadian_sovereignty_enforced": true,
  "evaluated_controls_count": 6,
  "satisfied_controls_count": 6,
  "summary": "ITSG-33 / PBMM Audit: 6/6 controls SATISFIED. Canadian Data Residency in ca-central-1: ENFORCED."
}
```
