# Service Level Agreement (SLA), High Availability & Disaster Recovery Specification

**Platform:** Aegis Continuity Sovereign SaaS & Infrastructure-as-Code Enclave  
**Target Availability:** 99.99% (Four Nines)  
**Target RPO / RTO:** Recovery Point Objective < 15 minutes • Recovery Time Objective < 60 minutes  
**Deployment Profile:** Sovereign Dual-Region Active-Active / Active-Standby  

---

## 1. Service Level Commitments

| Metric | Target SLA Commitment | Measurement Window | Failure Remedy / Credit |
| :--- | :--- | :--- | :--- |
| **Service Availability** | **99.99%** | Monthly Calendar Month | Tiered service credit: 10% for <99.99%, 25% for <99.9%, 50% for <99.0% |
| **API Response Latency (p95)** | **< 150 ms** | 1-hour rolling window | Automated horizontal pod autoscaling and read-replica routing |
| **Assessment Computation (p99)** | **< 2.0 s** | Per execution | Deterministic exact solver bounding limit (max 24 actions) |
| **Recovery Point Objective (RPO)** | **< 15 minutes** | Any disaster event | Continuous WAL streaming & point-in-time PostgreSQL replication |
| **Recovery Time Objective (RTO)** | **< 60 minutes** | Regional cloud outage | Automated DNS / Route 53 health failover to secondary Canadian region |

---

## 2. Dual-Region Sovereign Architecture (Canada Central & Canada East/West)

```text
┌────────────────────────────────────────────────────────────────────────┐
│               Global / Federal DNS & DDoS Protection (AWS/Azure WAF)    │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │ (Primary: 99.99%)              │ (Failover Standby)
┌───────────────────▼───────────────────┐ ┌──────────▼──────────────────────────┐
│   Region 1: AWS Montreal (ca-central) │ │    Region 2: AWS Calgary (ca-west)   │
│   • Multi-AZ EKS / ECS Cluster        │ │    • Warm Standby EKS / ECS Cluster  │
│   • Multi-AZ PostgreSQL Primary (CMK) │ │    • Read Replica PostgreSQL (CMK)   │
│   • Evidence Ledger Append S3 (CMK)   │ │    • Replicated S3 Evidence (CMK)    │
│   • Sovereign PrivateLink Endpoints   │ │    • Sovereign PrivateLink Endpoints │
└───────────────────────────────────────┘ └──────────────────────────────────────┘
```

### Data Synchronization & Cryptographic Invariants

1. **Cross-Region Evidence Ledger Replication:** Every append-only record is synchronized across Canadian regions via TLS 1.3 encrypted replication with SHA-256 integrity checks.
2. **Post-Quantum Zero Data Loss:** Point-in-time recovery enables restoration to any exact transaction timestamp within the 35-day backup retention window.
3. **Automated Drill Verification:** Quarterly simulated failover drills are executed using `scripts/restore_data.sh --confirm` against disposable environments.
