# Architecture

## System boundary

ContinuityOS is a decision-support control plane. It observes and recommends; it does not directly operate cyber-physical assets.

```text
Authoritative public data       Authenticated operator data
Climate, ice, weather,          Capacity, availability, cyber health,
imagery, traffic, trade         inventory, insurance, escort windows
             \                  /
              Source policy gate
                      |
              Immutable snapshots
                      |
            Normalized observations
                      |
       +--------------+---------------+
       |                              |
Dependency graph                Fusion engine
Cyber → physical impact         Risk + confidence + caveats
       |                              |
       +---------------+--------------+
                       |
              Continuity compiler
              Budget + constraints
                       |
              Human approval gate
                       |
              Signed evidence ledger
```

## Trust classes

1. **Authoritative public:** government or intergovernmental data that may support bounded factual claims.
2. **Open context:** useful public data that supports context but not live operational assertions.
3. **Authenticated operator:** customer-controlled telemetry permitted to assert live state within its scope.
4. **Analyst assessment:** structured judgments that must distinguish evidence, confidence, and scenario assumptions.

## Fail-closed rules

- Unknown sources are rejected.
- Source trust mismatches are rejected.
- Assertions outside a source's allow-list are rejected.
- Metric-to-assertion mismatches are rejected even when the source is otherwise trusted.
- Public context-only metrics cannot lower live operability risk or inflate live confidence.
- Analyst judgments require explicit epistemic status and an evidence basis.
- Expired observations are excluded.
- Missing required metrics reduce confidence and increase risk conservatively.
- Outbound HTTP is disabled by default.
- Production startup fails without evidence keys and operator webhook secret.
- The compiler rejects action sets above its exact bounded limit.
- Consequential actions retain a human-approval requirement.

## Determinism

Given the same normalized observations, explicit `as_of` time, graph, actions, and configuration, the risk and plan outputs are deterministic. External data is first captured as an immutable snapshot so a decision can be replayed later.

## Data model

- `Observation`: typed metric, assertion class, source trust, time, confidence, location, and hashed provenance.
- `CorridorAssessment`: factor risk, overall risk, state, confidence, missing data, and caveats.
- `DependencyGraph`: nodes and directed dependency edges from prerequisite to dependent.
- `GraphAssessment`: downstream impact probability, weighted impact, provider concentration, and SPOFs.
- `MitigationAction`: cost, gains, factor reductions, prerequisites, incompatibilities, lead time, and approval requirement.
- `CompiledPlan`: selected actions, projected continuity, cost, residual risk, and evidence of solver method.

## Scaling path

The reference exact compiler enumerates action subsets and is intentionally bounded. Production scale should use a mixed-integer solver adapter while retaining:

- deterministic input normalization;
- explicit constraints;
- reproducible solver version and seed;
- infeasibility explanation;
- evidence ledger output;
- human approval.
