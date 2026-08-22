import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Capabilities",
  description:
    "What the ContinuityOS Open-Core Engine actually does — sovereign assertion policy, deterministic fusion, cyber-physical dependency analysis, continuity compilation, and tamper-evident evidence ledger. And the boundaries it refuses to cross.",
  alternates: { canonical: "/capabilities" },
};

const CORE = [
  {
    title: "Sovereign assertion policy",
    body: "Source, metric, and assertion-class combinations are strictly enforced. Commercial orbiters cannot assert SCIF availability; the registry rejects out-of-scope claims.",
  },
  {
    title: "Air-gapped open-data snapshots",
    body: "Content-addressed cache with hashes and atomic writes for offline SCIF operations.",
  },
  {
    title: "Deterministic fusion engine",
    body: "Explicit replay time, factor-level risk, confidence, freshness decay, missing-data penalties, and explicit NATO APP-6D caveats.",
  },
  {
    title: "Functional closure classification",
    body: "Open, degraded, functionally closed, or physically closed — a defensible state label, not a vague “amber”.",
  },
  {
    title: "Cyber-physical dependency graph",
    body: "Downstream blast radius, provider concentration, substitution attenuation, and single-point-of-failure detection.",
  },
  {
    title: "Continuity compiler",
    body: "Exact bounded deterministic action selection under budget, prerequisites, incompatibilities, and human-in-the-loop approvals.",
  },
  {
    title: "Evidence ledger",
    body: "Append-only SHA-256 chain with optional Ed25519 signing and verification.",
  },
  {
    title: "Authenticated telemetry",
    body: "HMAC-SHA256 canonical webhook for operator assertions.",
  },
  {
    title: "FastAPI service and CLI",
    body: "Documented endpoints, health checks, source registry, assessment, graph analysis, plan compilation, evidence verification, snapshot import, and key generation.",
  },
  {
    title: "Offline-first controls",
    body: "Outbound HTTP disabled by default; cached snapshots remain reproducible without network access.",
  },
];

export default function Capabilities() {
  return (
    <div>
      <p className="eyebrow">Engine</p>
      <h1>Capabilities</h1>
      <p className="tagline">
        What the ContinuityOS Open-Core Engine actually does — and the boundaries
        it refuses to cross.
      </p>

      <h2>Core capabilities</h2>
      <ul className="feature-list">
        {CORE.map((c) => (
          <li key={c.title}>
            <span className="mk" aria-hidden="true">
              ✓
            </span>
            <div>
              <strong>{c.title}.</strong> {c.body}
            </div>
          </li>
        ))}
      </ul>

      <h2>Why this is different</h2>
      <p>
        Most systems stop at alerts, maps, or route recommendations. ContinuityOS
        connects observation to consequence to plan to signed evidence — and makes
        the whole chain replayable and auditable.
      </p>

      <div className="callout">
        <p>
          The defensible moat comes from validated customer dependency graphs,
          operator telemetry integrations, decision-outcome history, policy packs,
          and accreditation — not from public datasets alone.
        </p>
      </div>
    </div>
  );
}
