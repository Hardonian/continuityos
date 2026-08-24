# Sovereign RBAC, Multi-Tenant Isolation & Clearance Guide

## 1. Overview

Aegis Continuity implements defense-in-depth Role-Based Access Control (RBAC) and multi-tenant cryptographic isolation designed to meet the rigorous security requirements of the Canadian Department of National Defence (DND), NATO Allied Command Operations, and Tier-1 Defense Primes.

---

## 2. Multi-Tenant Architecture & Boundary Isolation

Every tenant (e.g., `DND-RCAF-TRENTON`, `CANADIAN-COAST-GUARD`, `TRANSPORT-CANADA-HQ`) operates within an isolated cryptographic namespace:

- **Isolated Evidence Ledgers**: Evidence records and SHA-256 state chains are compartmentalized by `tenant_id`.
- **Cross-Tenant Access Prevention**: Users belonging to one tenant enclave are strictly prohibited from reading or mutating policies, networks, or evidence in another tenant enclave.
- **Sovereign Commander Override**: Only identities holding the `SOVEREIGN_COMMANDER` role and Top Secret clearance can execute multi-enclave strategic audits.

---

## 3. Sovereign Role Hierarchy

| Role | Description | Core Authorizations |
| :--- | :--- | :--- |
| **`SOVEREIGN_COMMANDER`** | National Commander & Joint Task Force Chief | Cross-tenant global audits, wargaming, ledger signing, full administrative authority |
| **`TENANT_ADMIN`** | Local Base / Enclave Administrator | Tenant network mutations, policy evaluation, local user permissions |
| **`OPERATOR_ANALYST`** | Intelligence & Logistics Duty Officer | Telemetry ingestion, plan compilation, scenario wargaming, COP export |
| **`SECURITY_AUDITOR`** | Air-Gap & Cryptographic Compliance Auditor | Evidence ledger hash chain verification, ZKP verification, SCIF attestation |
| **`SCIF_AIRGAP_OPERATOR`** | Tactical Air-Gapped Node Specialist | DDIL Raft state log synchronization, physical media export, cluster peering |
| **`NATO_LIAISON_VIEWER`** | Allied Coalition Liaison Officer | Read-only access to sanitized unclassified / protected COP situational feeds |

---

## 4. Security Clearance Hierarchy & Dissemination Caveats

1. **Clearance Levels**:
   - `UNCLASSIFIED` (0)
   - `PROTECTED_A` (1)
   - `PROTECTED_B` (2)
   - `PROTECTED_C` (3)
   - `SECRET` (4)
   - `TOP_SECRET` (5)
   - `COSMIC_TOP_SECRET` (6)

2. **National Dissemination Controls**:
   - `CANADIAN_EYES_ONLY`: Requires verified Canadian citizenship (`citizenship_nation == "CAN"`).
   - `FIVE_EYES`: Limited to CAN, USA, GBR, AUS, NZL.
   - `NATO_SECRET`: Open to all 32 NATO member states with valid Secret clearances.
