import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Live Reference Deployment",
  description:
    "The current EPYC-hosted ContinuityOS reference API and Sovereign Defense Common Operating Picture dashboard.",
  alternates: { canonical: "/live" },
};

export default function Live() {
  return (
    <div>
      <p className="eyebrow">Deployment</p>
      <h1>Live Reference Deployment</h1>
      <p className="tagline">The current EPYC-hosted reference surface.</p>

      <p>
        The standalone evaluation and reference service is configured to run on loopback port <code>8082</code> or behind a sovereign ingress at{" "}
        <code>https://app.continuityos.com/</code>.
        It provides both an interactive Common Operating Picture and an air-gapped REST API control plane.
      </p>

      <h2>What is public</h2>
      <ul>
        <li>Health, readiness (<code>/readyz</code>, <code>/livez</code>), and source metadata are public.</li>
        <li>
          Assessment, compilation, and evidence ledger routes require{" "}
          <code>X-Continuity-API-Key</code> or Bearer token with appropriate RBAC roles.
        </li>
      </ul>

      <h2>Verify integrity</h2>
      <pre>
        <code>{`CONTINUITYOS_API_KEY=... bash scripts/smoke_live.sh http://127.0.0.1:8082`}</code>
      </pre>
      <p className="muted">
        Omit the key to verify that protected evidence is rejected. Deployment
        files and sovereign rollback runbooks are in <code>deploy/README.md</code>.
      </p>

      <h2>Interactive dashboard</h2>
      <p>
        The Sovereign Defense Common Operating Picture dashboard is available
        from the header (“COP Dashboard”) or directly at{" "}
        <Link href="/cop-dashboard.html">/cop-dashboard.html</Link>.
      </p>
    </div>
  );
}
