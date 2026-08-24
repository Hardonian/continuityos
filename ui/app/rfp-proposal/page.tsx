"use client";

import { useState } from "react";
import Link from "next/link";

interface ControlItem {
  id: string;
  name: string;
  family: string;
  status: "SATISFIED" | "PARTIALLY_SATISFIED";
  description: string;
  evidence: string;
}

const ITSG33_CONTROLS: ControlItem[] = [
  {
    id: "AC-2 / AC-3",
    name: "Account Management & Access Enforcement",
    family: "Access Control",
    status: "SATISFIED",
    description: "Enforce clearance levels (PROTECTED_B, SECRET) and Canadian Eyes Only controls.",
    evidence: "SecurityLabel.is_authorized() in sovereign.py with multi-level clearance comparison.",
  },
  {
    id: "AC-4",
    name: "Information Flow Enforcement & Cross-Domain Guards",
    family: "Access Control",
    status: "SATISFIED",
    description: "Prevent classification downgrade and sanitize internal cryptographic secrets.",
    evidence: "CrossDomainFilter in sovereign.py enforcing diode sanitization.",
  },
  {
    id: "SC-8",
    name: "Transmission Confidentiality & Integrity",
    family: "System and Comms",
    status: "SATISFIED",
    description: "Enforce TLS 1.3 in-transit and post-quantum hybrid cryptographic envelopes.",
    evidence: "Enforced TLS 1.3 reverse proxy route and ML-KEM / ML-DSA hybrid envelopes in crypto.py.",
  },
  {
    id: "SC-28",
    name: "Cryptographic Protection at Rest",
    family: "System and Comms",
    status: "SATISFIED",
    description: "AES-256-GCM / Customer Managed Keys (CMK) / CloudHSM encryption for all data.",
    evidence: "Terraform CMK key rotation and encrypted RDS / SQLite local enclave.",
  },
  {
    id: "AU-9",
    name: "Protection of Audit Records (Tamper-Evidence)",
    family: "Audit & Accountability",
    status: "SATISFIED",
    description: "Append-only SHA-256 evidence ledger with Ed25519 signatures and Merkle proofs.",
    evidence: "EvidenceLedger with atomic file replacement and Merkle inclusion proofs in crypto.py.",
  },
  {
    id: "MP-5",
    name: "Media Transport & Canadian Data Residency",
    family: "Media Protection",
    status: "SATISFIED",
    description: "Data strictly confined to Canadian sovereign cloud regions (ca-central-1, canadacentral).",
    evidence: "Terraform data residency validation rules and PBMMComplianceValidator region checks.",
  },
  {
    id: "CP-2",
    name: "Contingency Plan & Air-Gapped Operation",
    family: "Contingency Planning",
    status: "SATISFIED",
    description: "Zero-egress offline operation mode for military SCIF enclaves with mock telemetry.",
    evidence: "AirGapAuditor and standalone deploy/airgap_deploy.sh deployment script.",
  },
  {
    id: "SI-4",
    name: "Information System Monitoring & Cyber-Physical Threat Scan",
    family: "System Integrity",
    status: "SATISFIED",
    description: "Continuous telemetry scanning for GNSS spoofing, AIS kinematic jumps, and SCADA floods.",
    evidence: "threat.py ThreatDetectionEngine scanning incoming operational telemetry.",
  },
];

export default function RFPProposalPage() {
  const [activeTab, setActiveTab] = useState<"proposal" | "itsg33" | "itb" | "sla">("proposal");

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Government of Canada RFP &amp; Procurement Pack</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Sovereign SaaS &amp; IaC Proposal Suite
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Complete, turn-key bid proposal package tailored for PSPC, DND/CAF, SSC, and Transport Canada
          procurement solicitations requiring CCCS ITSG-33 Protected B compliance.
        </p>
      </header>

      {/* Navigation Tabs */}
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          borderBottom: "1px solid var(--border)",
          paddingBottom: "0.5rem",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
        }}
      >
        {[
          { id: "proposal", label: "📄 Executive Proposal & SOW" },
          { id: "itsg33", label: "🛡️ ITSG-33 PBMM Security Matrix" },
          { id: "itb", label: "🍁 Canadian Content & ITB Value" },
          { id: "sla", label: "⚡ 99.99% SLA & Disaster Recovery" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            style={{
              background: activeTab === t.id ? "var(--panel-2)" : "transparent",
              color: activeTab === t.id ? "var(--accent)" : "var(--muted)",
              border: activeTab === t.id ? "1px solid var(--accent)" : "1px solid transparent",
              borderRadius: "6px",
              padding: "0.5rem 1rem",
              fontWeight: 600,
              fontSize: "0.9rem",
              cursor: "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Executive Proposal & SOW */}
      {activeTab === "proposal" && (
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div
            style={{
              background: "rgba(56, 189, 248, 0.1)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: "6px",
              padding: "0.75rem 1rem",
              marginBottom: "1.5rem",
              fontSize: "0.85rem",
              color: "var(--accent)",
              fontFamily: "var(--mono)",
            }}
          >
            SOLICITATION TARGET: PSPC / DND / SSC ENTERPRISE SAAS &amp; RESILIENT INFRASTRUCTURE
          </div>

          <h2 style={{ fontSize: "1.4rem", marginBottom: "0.8rem" }}>Executive Summary</h2>
          <p style={{ color: "var(--text)", lineHeight: 1.7, marginBottom: "1.2rem" }}>
            Aegis Continuity is a deterministic Resilience-as-Code platform engineered specifically for
            Canadian Federal Government departments, National Defence, and critical infrastructure operators.
            Unlike legacy monitoring dashboards, Aegis Continuity models non-binary operational degradation,
            evaluates multi-tier supply chain dependencies, and executes exact bounded mitigation compilers
            under human-in-the-loop governance.
          </p>

          <h3 style={{ fontSize: "1.15rem", margin: "1.5rem 0 0.8rem 0" }}>5-Phase Statement of Work (SOW)</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
            {[
              {
                phase: "Phase 1: Enclave Initialization",
                duration: "Month 1",
                deliverable: "Deploy sovereign AWS Canada (ca-central-1) or Azure Canada Central enclave with ITSG-33 PBMM controls.",
              },
              {
                phase: "Phase 2: Graph & BOM Ingestion",
                duration: "Month 2",
                deliverable: "Ingest client multi-tier supply network topology, critical mineral dependencies, and transport nodes.",
              },
              {
                phase: "Phase 3: Public Data & Telemetry Integration",
                duration: "Month 3",
                deliverable: "Connect DFO IWLS, ECCC weather alerts, CCG ice operations, and GNSS spoofing telemetry feeds.",
              },
              {
                phase: "Phase 4: DRRS Readiness & COP Configuration",
                duration: "Month 4",
                deliverable: "Automate C-1 to C-5 defense readiness evaluations and export MIL-STD-2525D / NATO APP-6D COP overlays.",
              },
              {
                phase: "Phase 5: Air-Gap Verification & Training",
                duration: "Month 5",
                deliverable: "Pass air-gapped SCIF drill, disaster recovery failover drill, and operator certification.",
              },
            ].map((p, idx) => (
              <div
                key={idx}
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  padding: "0.9rem 1.2rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.2rem" }}>
                  <strong style={{ color: "var(--accent)" }}>{p.phase}</strong>
                  <span style={{ fontFamily: "var(--mono)", fontSize: "0.8rem", color: "var(--muted)" }}>
                    {p.duration}
                  </span>
                </div>
                <div style={{ fontSize: "0.88rem", color: "var(--text)" }}>{p.deliverable}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: ITSG-33 PBMM Security Matrix */}
      {activeTab === "itsg33" && (
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.2rem" }}>
            <h2 style={{ fontSize: "1.4rem", margin: 0 }}>CCCS ITSG-33 Protected B Control Matrix</h2>
            <span
              style={{
                background: "rgba(74, 222, 128, 0.15)",
                color: "var(--accent-2)",
                padding: "0.3rem 0.8rem",
                borderRadius: "4px",
                fontFamily: "var(--mono)",
                fontWeight: 700,
                fontSize: "0.85rem",
              }}
            >
              8 / 8 CORE CONTROLS SATISFIED
            </span>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                  <th style={{ padding: "0.6rem" }}>Control ID</th>
                  <th style={{ padding: "0.6rem" }}>Control Name &amp; Domain</th>
                  <th style={{ padding: "0.6rem" }}>Status</th>
                  <th style={{ padding: "0.6rem" }}>Architectural Evidence</th>
                </tr>
              </thead>
              <tbody>
                {ITSG33_CONTROLS.map((c) => (
                  <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.6rem", fontFamily: "var(--mono)", fontWeight: 700, color: "var(--accent)" }}>
                      {c.id}
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      <div style={{ fontWeight: 600 }}>{c.name}</div>
                      <div style={{ color: "var(--muted-2)", fontSize: "0.75rem" }}>{c.family}</div>
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      <span
                        style={{
                          background: "rgba(74, 222, 128, 0.15)",
                          color: "var(--accent-2)",
                          padding: "0.15rem 0.5rem",
                          borderRadius: "4px",
                          fontWeight: 700,
                          fontSize: "0.75rem",
                        }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem", color: "var(--muted)" }}>{c.evidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Canadian Content & ITB Value */}
      {activeTab === "itb" && (
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <h2 style={{ fontSize: "1.4rem", marginBottom: "0.8rem" }}>
            Industrial and Technological Benefits (ITB) &amp; Canadian Value Proposition
          </h2>
          <p style={{ color: "var(--text)", lineHeight: 1.7, marginBottom: "1.5rem" }}>
            Adopting Aegis Continuity enables defense prime contractors to claim <strong>100% Canadian Content Value (CCV)</strong> across
            the five core evaluation criteria mandated by ISED Canada and the Defence Investment Agency (DIA).
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "1rem",
            }}
          >
            {[
              {
                title: "100% Sovereign Canadian IP",
                body: "All algorithms, solvers, and cryptographic modules are developed within Canada, free from foreign export controls (ITAR-exempt).",
              },
              {
                title: "Domestic Cybersecurity R&D",
                body: "Continuous innovation in post-quantum cryptography (ML-DSA / ML-KEM), Merkle tree verification, and Explainable AI (XAI).",
              },
              {
                title: "Defense Prime Integration",
                body: "Seamless integration into major Canadian naval, aerospace, and land vehicle programs (NSS, AOPV, Polar Icebreaker, CPIC).",
              },
              {
                title: "Critical Mineral Safeguarding",
                body: "Direct support for Canada's Critical Minerals Strategy by securing domestic refining and battery cell manufacturing logistics.",
              },
            ].map((card, idx) => (
              <div
                key={idx}
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1.2rem",
                }}
              >
                <h3 style={{ fontSize: "1rem", color: "var(--accent-2)", marginBottom: "0.4rem" }}>
                  {card.title}
                </h3>
                <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: 0 }}>{card.body}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: 99.99% SLA & Disaster Recovery */}
      {activeTab === "sla" && (
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <h2 style={{ fontSize: "1.4rem", marginBottom: "0.8rem" }}>
            High Availability SLA &amp; Multi-Region Disaster Recovery
          </h2>
          <p style={{ color: "var(--text)", lineHeight: 1.7, marginBottom: "1.5rem" }}>
            Engineered for mission-critical defense and governmental operations with automated cross-region
            failover between <strong>AWS Canada Central (Montreal)</strong> and <strong>AWS Canada West (Calgary)</strong> or
            <strong>Azure Canada Central (Toronto)</strong> and <strong>Azure Canada East (Quebec City)</strong>.
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
              marginBottom: "1.5rem",
            }}
          >
            {[
              { label: "AVAILABILITY SLA", value: "99.99%", desc: "Four Nines Monthly Target" },
              { label: "RECOVERY POINT (RPO)", value: "< 15 min", desc: "Continuous WAL Replication" },
              { label: "RECOVERY TIME (RTO)", value: "< 60 min", desc: "Automated Regional DNS Failover" },
              { label: "ENCRYPTION AT REST", value: "AES-256", desc: "Customer Managed Key (CMK)" },
            ].map((stat, idx) => (
              <div
                key={idx}
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1rem",
                  textAlign: "center",
                }}
              >
                <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--accent)", margin: "0.2rem 0" }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--muted-2)" }}>{stat.desc}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem" }}>
        <Link href="/sovereign-compliance" className="btn btn-primary">
          Run Live Sovereign Compliance Audit →
        </Link>
        <Link href="/canadian-corridors" className="btn btn-ghost">
          Explore Canadian Corridors
        </Link>
      </div>
    </div>
  );
}
