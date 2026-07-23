# Threat Model

## Protected outcomes

- Integrity of corridor assessments and continuity plans
- Confidentiality of customer supply dependencies and inventory
- Availability of the decision-support service
- Provenance and non-repudiation of evidence records
- Separation of public context from authenticated operational assertions
- Prevention of unauthorized action execution

## Principal threats

### Data poisoning and false context

An attacker may inject false AIS, geospatial, weather, satellite, or analyst inputs. Controls:

- source registry and assertion allow-lists;
- immutable payload hashes;
- confidence and freshness scoring;
- independent-source comparison;
- missing-data penalties;
- explicit caveats;
- no automatic execution.

### Operator telemetry spoofing or replay

Controls:

- HMAC-SHA256 canonical body signatures;
- five-minute timestamp window;
- tenant and asset scoping in metadata;
- production secret requirements;
- recommended sequence-number replay store in production.

The reference implementation validates timestamps and signatures but does not persist replay sequence state. That is a documented production requirement.

### Evidence tampering

Controls:

- SHA-256 hash chain;
- optional Ed25519 signatures;
- atomic writes;
- independent public-key verification;
- recommended external WORM replication or transparency anchoring in production.

### Dependency graph disclosure

A detailed graph can reveal critical infrastructure concentration. Controls required in production:

- tenant isolation;
- attribute-based authorization;
- field-level encryption for sensitive attributes;
- export controls;
- immutable access audit;
- data minimization.

### Solver manipulation

Controls:

- bounded deterministic solver;
- explicit action prerequisites and incompatibilities;
- versioned action catalogue;
- budget constraints;
- objective and residual-risk reporting;
- mandatory human approval.

### Denial of service

Production controls should include request limits, payload limits, queue isolation, bounded graph size, execution deadlines, backpressure, circuit breakers, and degraded offline operation.

## Out of scope

- offensive cyber operations;
- targeting or interdiction;
- autonomous control of OT, vessels, drones, or weapons;
- classified intelligence ingestion;
- attribution of hostile activity;
- tactical force employment.
