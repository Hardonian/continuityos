import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ContinuityOS / Aegis Continuity — Sovereign Resilience-as-Code",
  description:
    "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains. Zero-cloud air-gapped deterministic engine.",
  alternates: { canonical: "/" },
};

const SOVEREIGN_PILLARS = [
  {
    icon: "🍁",
    badge: "CCCS ITSG-33 / PBMM",
    title: "Canadian Sovereign Corridors",
    body: "Real-time telemetry and assurance for the Ring of Fire, St. Lawrence Seaway, Port of Vancouver, and Trans-Canada rail networks under multi-modal degradation.",
    href: "/canadian-corridors",
    action: "View Corridors →",
  },
  {
    icon: "⚡",
    badge: "STRATEGIC BOM",
    title: "Critical Minerals Resilience",
    body: "Time-series stockpile depletion modeling, single-point-of-failure blast radius, and alternate refinery routing for nickel, lithium, cobalt, and rare earths.",
    href: "/critical-minerals",
    action: "Inspect Minerals BOM →",
  },
  {
    icon: "🎖️",
    badge: "NATO STANAG / DRRS",
    title: "Tactical War Room HUD",
    body: "Common Operating Picture (COP) with MIL-STD-2525D symbology, GNSS denial simulation, AIS spoofing detection, and automated C-Level readiness scoring.",
    href: "/war-room",
    action: "Launch War Room →",
  },
  {
    icon: "📄",
    badge: "GOVERNMENT RFP READY",
    title: "Defense RFP & Procurement Suite",
    body: "Turn-key bid compliance matrix, Statement of Work (SOW), ITB Canadian content verification, and 99.99% air-gapped SLA for PSPC and DND/CAF tenders.",
    href: "/rfp-proposal",
    action: "Review RFP Pack →",
  },
  {
    icon: "🔐",
    badge: "NIST FIPS 203 / 204",
    title: "Post-Quantum Cryptography",
    body: "Hybrid ML-KEM-768/1024 and ML-DSA-65/87 envelopes with Ed25519 fallbacks and zero-knowledge Merkle inclusion proofs for tamper-evident ledger integrity.",
    href: "/quantum-crypto",
    action: "Verify PQC Envelopes →",
  },
  {
    icon: "🛰️",
    badge: "EMCON / AIR-GAP",
    title: "Counter-Intel & SCIF Mesh",
    body: "Dark fleet spoofing detection, SAR satellite overflight avoidance, permafrost subsidence monitoring, and multi-node Raft state consensus over DDIL networks.",
    href: "/counter-intel",
    action: "Explore Counter-Intel →",
  },
];

export default function Home() {
  return (
    <div>
      {/* Sovereign Defense Status Ribbon */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 1rem",
          background: "rgba(15, 22, 32, 0.9)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          marginBottom: "2rem",
          fontSize: "0.85rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "#4ade80",
              boxShadow: "0 0 8px #4ade80",
              display: "inline-block",
            }}
          />
          <span style={{ fontWeight: 700, color: "var(--text)" }}>
            STANDALONE SOVEREIGN RUNTIME
          </span>
          <span style={{ color: "var(--muted)" }}>// ZERO-CLOUD AIR-GAP CERTIFIED</span>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <span
            style={{
              padding: "0.15rem 0.5rem",
              borderRadius: "4px",
              background: "rgba(56, 189, 248, 0.15)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              fontWeight: 600,
            }}
          >
            PROTECTED_B // PBMM
          </span>
          <span
            style={{
              padding: "0.15rem 0.5rem",
              borderRadius: "4px",
              background: "rgba(74, 222, 128, 0.15)",
              color: "#4ade80",
              border: "1px solid rgba(74, 222, 128, 0.3)",
              fontWeight: 600,
            }}
          >
            NATO C1 READINESS
          </span>
          <span
            style={{
              padding: "0.15rem 0.5rem",
              borderRadius: "4px",
              background: "rgba(251, 191, 36, 0.15)",
              color: "#fbbf24",
              border: "1px solid rgba(251, 191, 36, 0.3)",
              fontWeight: 600,
            }}
          >
            NIST PQC ML-KEM / ML-DSA
          </span>
        </div>
      </div>

      {/* Hero Section */}
      <section className="hero">
        <p className="eyebrow">Sovereign Defense &amp; Critical Infrastructure Assurance</p>
        <h1 style={{ fontSize: "clamp(2.2rem, 5vw, 3.4rem)", lineHeight: 1.15 }}>
          ContinuityOS
        </h1>
        <p className="tagline" style={{ maxWidth: "800px", margin: "1rem auto 2rem" }}>
          The canonical <strong>Resilience-as-Code</strong> platform engineered to evaluate,
          simulate, reconcile, and mathematically prove cyber-physical resilience across
          critical supply corridors, maritime chokepoints, and NATO mission logistics.
        </p>
        <div className="hero-actions">
          <Link href="/war-room" className="btn btn-primary" style={{ padding: "0.75rem 1.6rem" }}>
            Open Tactical War Room →
          </Link>
          <Link href="/rfp-proposal" className="btn btn-ghost" style={{ padding: "0.75rem 1.6rem" }}>
            Government RFP / PBMM Pack
          </Link>
          <Link href="/quickstart" className="btn btn-ghost" style={{ padding: "0.75rem 1.6rem" }}>
            Local CLI Quickstart
          </Link>
        </div>
      </section>

      {/* Executive Core Value & Invariant Anchor */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "1.75rem",
          margin: "2.5rem 0",
        }}
      >
        <h2 style={{ margin: "0 0 1rem", fontSize: "1.3rem", color: "var(--accent)" }}>
          The Fundamental Resilience Invariant
        </h2>
        <p className="lede" style={{ margin: 0, fontSize: "1.05rem" }}>
          Traditional Infrastructure-as-Code verifies configuration. Kubernetes reconciles desired containers.
          <strong> ContinuityOS answers the consequential question:</strong>
          <br />
          <em>
            &ldquo;Will your supply corridor, fuel depot, or defense logistics network function through
            GNSS jamming, cyber SCADA lockout, underwriter withdrawal, and cascading chokepoints — and what exact,
            provably bounded actions restore continuity?&rdquo;
          </em>
        </p>
      </div>

      {/* 6 Sovereign Pillars */}
      <h2 style={{ fontSize: "1.6rem", marginTop: "3rem" }}>Sovereign Operational Modules</h2>
      <p className="muted" style={{ marginBottom: "1.5rem" }}>
        Every module operates with 100% deterministic reproducibility, zero mandatory cloud egress, and complete cryptographic provenance.
      </p>
      <div className="card-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))" }}>
        {SOVEREIGN_PILLARS.map((p) => (
          <div
            className="card"
            key={p.title}
            style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "1.5rem",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <span style={{ fontSize: "1.8rem" }}>{p.icon}</span>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "0.2rem 0.5rem",
                    borderRadius: "4px",
                    background: "var(--panel-2)",
                    color: "var(--accent)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {p.badge}
                </span>
              </div>
              <h3 style={{ margin: "0.5rem 0", fontSize: "1.15rem" }}>{p.title}</h3>
              <p style={{ color: "var(--muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
                {p.body}
              </p>
            </div>
            <div style={{ marginTop: "1.25rem" }}>
              <Link href={p.href} style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--accent)" }}>
                {p.action}
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* The 6-Stage Deterministic Exact Solver Chain */}
      <h2 style={{ fontSize: "1.6rem", marginTop: "3.5rem" }}>The 6-Stage Deterministic Exact-Solver Chain</h2>
      <div className="chain">
        {[
          "1. Source-Qualified Telemetry (No Blind Trust)",
          "2. Cyber-Physical Dependency Impact Mapping",
          "3. 12-State Operational Corridor Classification",
          "4. Feasible Mitigation Candidate Pruning",
          "5. Bounded Mitigation Plan Exact Compilation",
          "6. Ed25519 & PQC Cryptographically Signed Evidence",
        ].map((step, i) => (
          <div className="chain-step" key={step}>
            <span className="n">{i + 1}</span>
            <code>{step}</code>
          </div>
        ))}
      </div>

      {/* Declarative DSL Sample */}
      <h2 style={{ fontSize: "1.6rem", marginTop: "3.5rem" }}>Declarative Resilience-as-Code Spec</h2>
      <p className="muted">
        Define resilient networks as human-readable, machine-verifiable YAML resources conforming to <code>continuity.io/v1</code>.
      </p>
      <pre
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "1.25rem",
          overflowX: "auto",
          fontSize: "0.88rem",
          color: "var(--text)",
        }}
      >
        <code>{`apiVersion: continuity.io/v1
kind: SupplyNetwork
metadata:
  name: ontario-ring-of-fire-corridor
  classification: PROTECTED_B
  eyesOnly: CANADIAN_EYES_ONLY
spec:
  corridor: RingOfFireToWindsorGiga
  desiredContinuityDays: 60
  minimumRedundancy:
    railProviders: 2
    iceClassBarges: 4
    fuelDaysReserve: 45
  tolerances:
    maxPermafrostDegradationRate: 0.12
    gnssSpoofingSensitivity: HIGH
    pqcEnvelopeRequired: true
  recoveryConstraints:
    maxAcceptableDowntimeDays: 5
    criticalPathSolver: BOUNDED_EXACT_SOLVER`}</code>
      </pre>

      {/* Defensive Safety ROE */}
      <h2 style={{ fontSize: "1.6rem", marginTop: "3.5rem" }}>Defensive Safety Boundary &amp; Rules of Engagement (ROE)</h2>
      <div className="callout danger">
        <p>
          <strong>ContinuityOS operates strictly as an advisory resilience planning and intelligence engine.</strong> It
          does not autonomously dispatch kinetic vehicles, execute port SCADA switches, or run consequential cyber actions.
          All compiled recovery plans require explicit, authenticated human-in-the-loop sign-off before implementation.
        </p>
      </div>

      {/* Footer Navigation Bar */}
      <div
        style={{
          marginTop: "3rem",
          padding: "1.5rem",
          background: "var(--panel)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <strong style={{ display: "block" }}>Ready for Sovereign Government Evaluation?</strong>
          <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Download the complete Canadian PBMM / ITSG-33 Bid Compliance Package.
          </span>
        </div>
        <div style={{ display: "flex", gap: "1rem" }}>
          <Link href="/rfp-proposal" className="btn btn-primary">
            View Bid Proposal Suite →
          </Link>
          <Link href="/live" className="btn btn-ghost">
            Inspect Architecture
          </Link>
        </div>
      </div>
    </div>
  );
}
