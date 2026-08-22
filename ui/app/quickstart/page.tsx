import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Quickstart",
  description:
    "Run the ContinuityOS reference engine locally in a few minutes — Python venv, Docker, integrity verification, and project layout.",
  alternates: { canonical: "/quickstart" },
};

export default function Quickstart() {
  return (
    <div>
      <p className="eyebrow">Get started</p>
      <h1>Quickstart</h1>
      <p className="tagline">Run the reference engine locally in a few minutes.</p>

      <h2>Local</h2>
      <pre>
        <code>{`python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make verify
make demo
uvicorn continuityos.service:app --host 127.0.0.1 --port 8080`}</code>
      </pre>

      <h2>Docker</h2>
      <pre>
        <code>{`bash scripts/docker_bootstrap.sh
docker compose build
docker compose up
curl http://127.0.0.1:8080/healthz`}</code>
      </pre>
      <p className="muted">
        The container has no outbound data access unless{" "}
        <code>CONTINUITYOS_OUTBOUND_HTTP_ENABLED=true</code> is explicitly set.
      </p>

      <h2>Verify authenticated integrity</h2>
      <pre>
        <code>{`CONTINUITYOS_API_KEY=... bash scripts/smoke_live.sh https://aiautomatedsystems.ca/continuityos`}</code>
      </pre>
      <p>
        Omit the key to verify that protected evidence is rejected. Health and
        source metadata are public; assessment, compilation, and evidence routes
        require <code>X-Continuity-API-Key</code>.
      </p>

      <h2>Project layout</h2>
      <ul>
        <li>
          <code>src/continuityos/</code> — engine, service, sources, graph, plans
        </li>
        <li>
          <code>examples/</code> — dependency graphs (e.g.
          arctic_dependency_graph.yaml)
        </li>
        <li>
          <code>deploy/</code> — deployment files and rollback notes
        </li>
        <li>
          <code>docs/</code> — architecture, data sources, posture, procurement
          research
        </li>
      </ul>
    </div>
  );
}
