# ContinuityOS — Open-Core Commercialization Model & Pricing Strategy

This document outlines the commercial packaging, tiering architecture, and pricing strategy for **ContinuityOS**.

---

## 1. Open-Core Principles & Boundary

ContinuityOS adheres to strict open-core integrity:
- **No Crippled Core**: The open-source core is fully functional, capable of running complete local-first simulations, plan compilations, and air-gapped reconciliations.
- **Developer First**: Individual engineers, researchers, and emergency response teams can model arbitrary networks without contacting sales.
- **Enterprise Expansion**: Commercial value is captured through enterprise collaboration, centralized management, compliance integration, and managed data feeds.

---

## 2. Product Packaging Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           CONTINUITYOS INTELLIGENCE                              │
│  * Curated Historical Disruption Datasets  * Pre-Trained Bayesian Risk Models    │
│  * Authoritative Commercial Data Feeds     * Industry-Specific Corridor Packs    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                            CONTINUITYOS ENTERPRISE                               │
│  * Centralized Web Control Plane           * Sovereign Air-Gap & SCIF Appliances │
│  * Enterprise SSO / SAML / OIDC            * Fine-Grained Role-Based Access (RBAC│
│  * Immutable Multi-Tenant Evidence Vault   * Regulatory Compliance Export Packs  │
│  * ERP & WMS Enterprise Connectors         * High-Availability Cluster Orchestr  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                        CONTINUITYOS CORE (OPEN SOURCE)                           │
│  * Declarative YAML DSL (v1)               * Bounded Exact Solver Plan Compiler  │
│  * 12-State Composable Closure Engine      * Multi-Factor Dependency Trust Engine│
│  * Cyber-Physical Dependency Graph Engine  * Correlated Scenario Runner          │
│  * Strategic Inventory Depletion Engine    * T0-T5 Recovery Lag Engine           │
│  * Route Substitution Compiler             * Provider Independence Analyzer      │
│  * Assurance-as-Code Budgeting Engine      * Append-Only Evidence Ledger         │
│  * Zero-Cloud CLI & Offline Providers      * Public Reference Architectures      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Edition Comparison

| Feature | Open Source Core (Apache 2.0) | Enterprise Edition | Sovereign / Defense Edition |
| :--- | :---: | :---: | :---: |
| **Deployment Mode** | Local CLI / Embedded Library | Cloud / On-Prem Kubernetes | Air-Gapped SCIF Appliance |
| **Declarative DSL & CLI** | ✅ Full Surface | ✅ Full Surface | ✅ Full Surface |
| **Deterministic Solver Engines** | ✅ All 6 Engines | ✅ All 6 Engines | ✅ All 6 Engines |
| **Max Resources** | Unlimited (Workstation RAM) | Scaled Distributed DB | Scaled Air-Gap DB |
| **Central Web Dashboard** | ❌ (CLI / JSON output) | ✅ Multi-User Web UI | ✅ High-Security Web UI |
| **Authentication & IAM** | Local Filesystem / API Keys | Enterprise SSO / RBAC | PKI / CAC / Sovereign Labels |
| **Multi-Tenancy** | Single Workspace | Multi-Org / Multi-Team | Cross-Domain Enclave Guards |
| **Evidence Storage** | Local JSONL Ledger | Tamper-Evident Object Store | Hardware HSM / PQC Ledger |
| **Support SLA** | Community GitHub Discussions | 99.9% SLA & Dedicated Lead | 24/7 Cleared Support Engineers |

---

## 4. Pricing Strategy & Monetization Hypothesis

We recommend the simplest viable enterprise model: **per-managed-network annual subscription**, avoiding complex per-ping or per-gigabyte usage pricing.

### Tier 1: Open Source Core
- **Cost**: **$0 (Free, Open Source under Apache 2.0)**
- **Target**: Individual platform engineers, academic researchers, disaster relief teams.
- **Includes**: Complete CLI, all core engines, local evidence ledger, mock providers, and schemas.

### Tier 2: Enterprise Team
- **Cost**: **$48,000 / year** (includes up to 5 Managed Networks, up to 500 resources).
- **Target**: Regional energy operators, mid-sized manufacturing, hospital networks.
- **Includes**: Centralized web control plane, GitOps PR bot, enterprise SSO, automated drift alerting, standard SLA support.

### Tier 3: Enterprise Strategic
- **Cost**: **$180,000 / year** (unlimited networks, enterprise-wide deployment).
- **Target**: Global Tier-1 defense primes, multinational maritime logistics, global pharmaceutical manufacturers.
- **Includes**: Dedicated deployment engineers, custom ERP connectors, multi-tenant workspace isolation, prioritized feature roadmap.

### Tier 4: Sovereign / Defense Enclave
- **Cost**: **Custom Annual Contract ($350k - $750k+)**
- **Target**: Ministries of Defense, National Security Agencies, Sovereign Critical Infrastructure Authorities.
- **Includes**: Air-gapped SCIF deployment packages, NATO APP-6D COP integration, cross-domain security guards, post-quantum cryptographic envelopes, and cleared support.
