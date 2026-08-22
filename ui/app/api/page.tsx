import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "API",
  description:
    "Documented, authenticated ContinuityOS API endpoints. Health and source metadata are public; assessment, compilation, and evidence routes require an API key.",
  alternates: { canonical: "/api" },
};

export default function Api() {
  return (
    <div>
      <p className="eyebrow">Reference</p>
      <h1>API</h1>
      <p className="tagline">
        Documented, authenticated endpoints. Health and source metadata are
        public; assessment, compilation, and evidence routes require an API key.
      </p>

      <h2>Assess a corridor</h2>
      <pre>
        <code>{`POST /v1/assess        (requires X-Continuity-API-Key)

{
  "corridor_id": "northwest-passage-west",
  "observations": []
}`}</code>
      </pre>
      <p className="muted">
        Observations must pass the registry rules in{" "}
        <code>src/continuityos/sources/registry.py</code>.
      </p>

      <h2>Analyze cyber-physical blast radius</h2>
      <pre>
        <code>{`POST /v1/graph/analyze?failed_nodes=shared-idp&failed_nodes=satcom-a
                          (requires X-Continuity-API-Key)

Body: a DependencyGraph (e.g. examples/arctic_dependency_graph.yaml as JSON)`}</code>
      </pre>

      <h2>Compile a continuity plan</h2>
      <pre>
        <code>{`POST /v1/compile        (requires X-Continuity-API-Key)`}</code>
      </pre>
      <p className="muted">
        The compiler is exact for up to 24 actions by default. It rejects larger
        unbounded plans rather than silently using a heuristic. A production
        OR-Tools adapter can implement the same evidence contract for larger
        action sets.
      </p>

      <h2>Generate a complete decision packet</h2>
      <pre>
        <code>{`POST /v1/decision-packets   (requires X-Continuity-API-Key)`}</code>
      </pre>
      <p>
        The high-leverage orchestration surface: one bounded, idempotent request
        produces a corridor assessment, dependency blast-radius analysis,
        deterministic mitigation plan, evidence manifest, approval requirement,
        and explicit human-action boundary. It records the packet and component
        results in the signed evidence ledger. It never executes, dispatches, or
        authorizes consequential actions.
      </p>

      <h2>Strategic signal analysis</h2>
      <pre>
        <code>{`POST /v1/strategic/analyze   (requires X-Continuity-API-Key)
GET  /v1/strategic/stream?duration_seconds=15
POST /v1/strategic/alerts/{alert_key}/ack
POST /v1/strategic/alerts/{alert_key}/unack`}</code>
      </pre>
      <p className="muted">
        Computes a freshness- and confidence-weighted multivariate heatmap,
        ranked explainable alerts, and human-gated coordination recommendations.
        Predictive status remains explicit; no output is represented as causal
        truth, validated forecasting, autonomous coordination, or dispatch.
      </p>
    </div>
  );
}
