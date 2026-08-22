import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aegis Continuity — Sovereign Resilience-as-Code",
  description:
    "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains. Powered by the ContinuityOS Open-Core Engine.",
  alternates: { canonical: "/" },
};

const CAPS = [
  {
    icon: "🛡️",
    title: "Sovereign assertion policy",
    body: "Source, metric, and assertion-class combinations are strictly enforced — commercial orbiters cannot assert SCIF availability.",
  },
  {
    icon: "🧮",
    title: "Deterministic fusion",
    body: "Explicit replay time, factor-level risk, confidence, freshness decay, missing-data penalties, and NATO APP-6D caveats.",
  },
  {
    icon: "🗺️",
    title: "Continuity compiler",
    body: "Exact bounded deterministic action selection under budget, prerequisites, incompatibilities, and human-in-the-loop approvals.",
  },
  {
    icon: "🔗",
    title: "Evidence ledger",
    body: "Append-only SHA-256 chain with optional Ed25519 signing and verification. Tamper-evident decision evidence.",
  },
];

export default function Home() {
  return (
    <div>
      <section className="hero">
        <p className="eyebrow">Defense &amp; Maritime Continuity Assurance</p>
        <h1>Aegis Continuity</h1>
        <p className="tagline">
          Sovereign Resilience-as-Code and cyber-physical continuity assurance
          for critical maritime corridors, NATO logistics, Arctic operations, and
          defense supply chains.
        </p>
        <div className="hero-actions">
          <Link href="/capabilities" className="btn btn-primary">
            Explore capabilities →
          </Link>
          <Link href="/live" className="btn btn-ghost">
            Live reference deployment
          </Link>
        </div>
      </section>

      <p className="lede">
        A deterministic, air-gapped Reference Architecture designed for Ministries
        of Defense and Tier-1 Defense Primes. It is <strong>not</strong> an
        autonomous controller or a kinetic command system. It ingests bounded
        observations, enforces source-assertion policy, estimates corridor
        operability, maps cyber failures to physical supply consequences,
        compiles a cost-constrained continuity plan, and writes tamper-evident
        decision evidence to a post-quantum secure ledger.
      </p>

      <h2>The chain most systems stop short of</h2>
      <div className="chain">
        {[
          "source-qualified observation",
          "cyber-physical dependency impact",
          "operational corridor state",
          "feasible mitigation set",
          "costed continuity plan",
          "signed decision and outcome evidence",
        ].map((step, i) => (
          <div className="chain-step" key={step}>
            <span className="n">{i + 1}</span>
            <code>{step}</code>
          </div>
        ))}
      </div>
      <p className="muted">
        The reference implementation makes that chain testable and deterministic.
        The defensible moat comes from validated customer dependency graphs,
        operator telemetry integrations, decision-outcome history, policy packs,
        and accreditation — not from public datasets alone.
      </p>

      <h2>What is implemented</h2>
      <div className="card-grid">
        {CAPS.map((c) => (
          <div className="card" key={c.title}>
            <span className="icon" aria-hidden="true">
              {c.icon}
            </span>
            <h3>{c.title}</h3>
            <p>{c.body}</p>
          </div>
        ))}
      </div>

      <h2>Safety boundary</h2>
      <div className="callout danger">
        <p>
          <strong>Aegis Continuity acts strictly as an advisory intelligence
          overlay.</strong> It does not execute autonomous kinetic actions,
          control OT or port SCADA, treat public satellite catalogues as proof of
          secure communications, or run any consequential mitigation without
          explicit, accountable human authorization.
        </p>
      </div>

      <p style={{ marginTop: "2rem" }}>
        <Link href="/capabilities" className="text-link">
          Explore full capabilities →
        </Link>
      </p>
    </div>
  );
}
