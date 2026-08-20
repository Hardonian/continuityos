export default function Capabilities() {
  return (
    <div>
      <h1>Capabilities</h1>
      <p className="tagline">
        What the ContinuityOS Open-Core Engine actually does — and the boundaries it
        refuses to cross.
      </p>

      <h2>Core capabilities</h2>
      <ul>
        <li>
          <strong>Sovereign assertion policy.</strong> Source, metric, and
          assertion-class combinations are strictly enforced. Commercial orbiters
          cannot assert SCIF availability; the registry rejects out-of-scope claims.
        </li>
        <li>
          <strong>Air-gapped open-data snapshots.</strong> Content-addressed cache
          with hashes and atomic writes for offline SCIF operations.
        </li>
        <li>
          <strong>Deterministic fusion engine.</strong> Explicit replay time,
          factor-level risk, confidence, freshness decay, missing-data penalties, and
          explicit NATO APP-6D caveats.
        </li>
        <li>
          <strong>Functional closure classification.</strong> Open, degraded,
          functionally closed, or physically closed — a defensible state label, not a
          vague &ldquo;amber&rdquo;.
        </li>
        <li>
          <strong>Cyber-physical dependency graph.</strong> Downstream blast radius,
          provider concentration, substitution attenuation, and single-point-of-failure
          detection.
        </li>
        <li>
          <strong>Continuity compiler.</strong> Exact bounded deterministic action
          selection under budget, prerequisites, incompatibilities, and
          human-in-the-loop approvals.
        </li>
        <li>
          <strong>Evidence ledger.</strong> Append-only SHA-256 chain with optional
          Ed25519 signing and verification.
        </li>
        <li>
          <strong>Authenticated telemetry.</strong> HMAC-SHA256 canonical webhook for
          operator assertions.
        </li>
        <li>
          <strong>FastAPI service and CLI.</strong> Documented endpoints, health
          checks, source registry, assessment, graph analysis, plan compilation,
          evidence verification, snapshot import, and key generation.
        </li>
        <li>
          <strong>Offline-first controls.</strong> Outbound HTTP disabled by default;
          cached snapshots remain reproducible without network access.
        </li>
      </ul>

      <h2>Why this is different</h2>
      <p>
        Most systems stop at alerts, maps, or route recommendations. ContinuityOS
        connects observation to consequence to plan to signed evidence — and makes the
        whole chain replayable and auditable.
      </p>
    </div>
  );
}
