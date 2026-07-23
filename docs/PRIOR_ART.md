# Prior Art and Novelty Boundary

## Purpose

This document prevents ContinuityOS from being represented as novel merely because it combines familiar technologies. It separates established methods from the narrower engineering claims that may be defensible after professional legal review.

## Established prior art

The following are established and are **not** claimed as novel in isolation:

- maritime common operating pictures, vessel tracking, and geospatial dashboards;
- digital twins for ports, transport corridors, and cyber-physical systems;
- graph-based supply-chain and infrastructure dependency analysis;
- stochastic and mixed-integer logistics optimization;
- business-continuity and operational-resilience planning;
- infrastructure-as-code and policy-as-code;
- event sourcing, append-only logs, cryptographic hashes, and digital signatures;
- cybersecurity monitoring for ports, vessels, satellite services, and operational technology;
- sea-ice, weather, Earth-observation, orbital, port, AIS, and trade datasets;
- risk scoring, anomaly detection, scenario analysis, and recovery-time estimation.

Relevant standards and public research include:

- NIST SP 800-82 Rev. 3, *Guide to Operational Technology Security*;
- NIST SP 800-161 Rev. 1 Update 1, *Cybersecurity Supply Chain Risk Management Practices*;
- IMO maritime cyber-risk-management guidance;
- research on maritime-port supply-chain resilience;
- research on correlated chokepoint disruption and logistics optimization;
- research on digital twins for cyber-physical corridors and smart ports.

## Bounded differentiating mechanism

The reference implementation demonstrates a specific closed loop:

```text
source-qualified observation
→ assertion-policy enforcement
→ cyber-to-physical dependency propagation
→ functional-operability assessment
→ constrained continuity compilation
→ human authorization
→ signed, replayable decision evidence
```

The potentially differentiating aspects are the implementation boundaries between these stages:

1. **Assertion-capability policy**
   A source is authorized to support only defined assertion classes. Static port records, orbital elements, public imagery metadata, and historical traffic cannot assert live capacity, cyber health, insurance access, or communications availability.

2. **Cyber-to-logistics consequence propagation**
   A digital-service failure is evaluated through a dependency graph to determine operational effects on ports, communications, inventory, routes, and supply objectives.

3. **Functional closure rather than physical closure**
   Corridor state incorporates availability, integrity, logistics support, commercial confidence, observation freshness, and unresolved evidence gaps. A corridor can be geographically open while operationally or commercially unusable.

4. **Objective-to-action compilation**
   The system converts a declared continuity threshold, budget, prerequisites, and incompatibilities into a deterministic, costed mitigation set. It rejects unbounded search rather than presenting an unexplained heuristic as an optimal plan.

5. **Evidence-bearing analysis**
   Assessments and plans preserve source identity, timestamps, content hashes, method versions, constraints, selected actions, approvals, and later outcomes so a decision can be independently replayed.

6. **Offline and sovereign reproducibility**
   External information is converted into immutable content-addressed snapshots. Assessments can be repeated in disconnected environments without silently fetching newer data.

## Defensibility assessment

### Strongest potential moat

- validated customer dependency graphs;
- authenticated operator and insurer integrations;
- calibrated functional-closure and recovery models;
- decision-to-outcome history;
- jurisdiction, sanctions, safety, and continuity policy packs;
- sovereign deployment accreditation and trusted operating history.

### Weak moat

- public datasets;
- generic dashboards;
- a weighted risk score;
- an LLM-generated briefing;
- ordinary route optimization;
- container orchestration or infrastructure-as-code alone.

## Patent and freedom-to-operate position

This repository makes no patentability, novelty, non-obviousness, or freedom-to-operate claim. Before filing or commercialization:

1. commission a professional prior-art and claim search;
2. map each proposed claim to a concrete mechanism and test;
3. compare claims against maritime digital-twin, logistics-optimization, graph-risk, and signed-decision systems;
4. review third-party software and data licences;
5. preserve dated design records and experimental evidence;
6. decide which mechanisms remain trade secrets rather than patent disclosures.

## Reference links

- NIST SP 800-82 Rev. 3: https://csrc.nist.gov/pubs/sp/800/82/r3/final
- NIST SP 800-161 Rev. 1 Update 1: https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final
- IMO maritime cyber-risk management: https://www.imo.org/en/ourwork/security/pages/cyber-security.aspx
- NOAA@NSIDC Sea Ice Index: https://nsidc.org/data/g02135
- ECCC MSC GeoMet: https://api.weather.gc.ca/
- Copernicus Data Space STAC: https://stac.dataspace.copernicus.eu/v1/
