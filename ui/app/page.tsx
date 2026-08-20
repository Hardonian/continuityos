import Link from "next/link";

export default function Home() {
  return (
    <div>
      <h1>Aegis Continuity</h1>
      <p className="tagline">
        Sovereign Resilience-as-Code and cyber-physical continuity assurance for
        critical maritime corridors, NATO logistics, Arctic operations, and defense
        supply chains.
      </p>
      <p>
        A deterministic, air-gapped Reference Architecture designed for Ministries of
        Defense and Tier-1 Defense Primes. It is <strong>not</strong> an autonomous
        controller or a kinetic command system. It ingests bounded observations,
        enforces source-assertion policy, estimates corridor operability, maps cyber
        failures to physical supply consequences, compiles a cost-constrained
        continuity plan, and writes tamper-evident decision evidence to a
        post-quantum secure ledger.
      </p>

      <h2>The chain most systems stop short of</h2>
      <pre><code>{`source-qualified observation
→ cyber-physical dependency impact
→ operational corridor state
→ feasible mitigation set
→ costed continuity plan
→ signed decision and outcome evidence`}</code></pre>
      <p className="muted">
        The reference implementation makes that chain testable and deterministic. The
        defensible moat comes from validated customer dependency graphs, operator
        telemetry integrations, decision-outcome history, policy packs, and
        accreditation — not from public datasets alone.
      </p>

      <h2>What is implemented</h2>
      <div className="card-grid">
        <div className="card">
          <h3>Sovereign assertion policy</h3>
          <p className="muted">
            Source, metric, and assertion-class combinations are strictly enforced
            (e.g., commercial orbiters cannot assert SCIF availability).
          </p>
        </div>
        <div className="card">
          <h3>Deterministic fusion</h3>
          <p className="muted">
            Explicit replay time, factor-level risk, confidence, freshness decay,
            missing-data penalties, and NATO APP-6D caveats.
          </p>
        </div>
        <div className="card">
          <h3>Continuity compiler</h3>
          <p className="muted">
            Exact bounded deterministic action selection under budget,
            prerequisites, incompatibilities, and human-in-the-loop approvals.
          </p>
        </div>
        <div className="card">
          <h3>Evidence ledger</h3>
          <p className="muted">
            Append-only SHA-256 chain with optional Ed25519 signing and
            verification. Tamper-evident decision evidence.
          </p>
        </div>
      </div>

      <h2>Safety boundary</h2>
      <p>
        Aegis Continuity acts strictly as an <strong>advisory intelligence
        overlay</strong>. It does not execute autonomous kinetic actions, control OT
        or port SCADA, treat public satellite catalogues as proof of secure
        communications, or run any consequential mitigation without explicit,
        accountable human authorization.
      </p>

      <Link href="/capabilities" className="cta">
        Explore capabilities
      </Link>
    </div>
  );
}
