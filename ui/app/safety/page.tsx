import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Safety, Authority & ROE Boundary",
  description:
    "Aegis Continuity acts strictly as an advisory intelligence overlay. It does not execute autonomous kinetic actions, control OT or port SCADA, or authorize consequential mitigations without accountable human authorization.",
  alternates: { canonical: "/safety" },
};

export default function Safety() {
  return (
    <div>
      <p className="eyebrow">Governance</p>
      <h1>Safety, Authority &amp; ROE Boundary</h1>
      <p className="tagline">
        Aegis Continuity acts strictly as an advisory intelligence overlay.
      </p>

      <div className="callout danger">
        <p>
          <strong>It does not:</strong>
        </p>
        <ul>
          <li>
            execute autonomous kinetic actions, weapons targeting, or
            interdiction operations;
          </li>
          <li>
            control operational technology (OT), port SCADA, or maritime
            uncrewed surface vessels (USVs);
          </li>
          <li>
            treat public satellite catalogues as proof of secure communications
            availability;
          </li>
          <li>
            infer current strategic port capacity from static geospatial
            intelligence (GEOINT);
          </li>
          <li>
            execute any consequential mitigations without explicit, accountable
            human-in-the-loop authorization.
          </li>
        </ul>
      </div>

      <h2>Human-in-the-loop by design</h2>
      <p>
        The continuity compiler produces a costed, prerequisite-aware plan and an
        explicit approval requirement. The boundary between recommendation and
        action is always a named human decision. The evidence ledger records who
        approved what, when, and under which policy pack.
      </p>

      <h2>Source-assertion policy</h2>
      <p>
        Not every signal is allowed to assert every state. The registry enforces
        source–metric–assertion-class combinations so that, for example, a
        commercial orbiter cannot assert SCIF availability. This prevents
        low-trust sources from contaminating high-consequence decisions.
      </p>

      <h2>Determinism as accountability</h2>
      <p>
        Because fusion and planning are deterministic and replayable, any
        decision can be reconstructed exactly: same inputs, same replay time,
        same result. That makes the system auditable after the fact — essential
        for accreditation and post-incident review.
      </p>
    </div>
  );
}
