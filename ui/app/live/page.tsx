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
        The live evaluation/reference API is available at{" "}
        <a href="https://aiautomatedsystems.ca/continuityos/">
          https://aiautomatedsystems.ca/continuityos/
        </a>
        . It is intentionally an evaluation/reference API, not a tenant-isolated
        customer control plane.
      </p>

      <h2>What is public</h2>
      <ul>
        <li>Health and source metadata are public.</li>
        <li>
          Assessment, compilation, and evidence routes require{" "}
          <code>X-Continuity-API-Key</code>.
        </li>
      </ul>

      <h2>Verify integrity</h2>
      <pre>
        <code>{`CONTINUITYOS_API_KEY=... bash scripts/smoke_live.sh https://aiautomatedsystems.ca/continuityos`}</code>
      </pre>
      <p className="muted">
        Omit the key to verify that protected evidence is rejected. Deployment
        files and rollback notes are in <code>deploy/README.md</code>.
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
