# Canadian Contract and System Positioning Notes (2025-current)

This is a public-source market and positioning brief, not legal advice, procurement advice, or evidence of access to any government system.

## Observed procurement signals

### Arctic SATCOM and sovereign communications

CanadaBuys contract history for Enhanced Satellite Communication Project - Polar identifies Telesat Canada, DND/PSPC, a 2025-11-03 award, and Arctic beyond-line-of-sight SATCOM engineering/services. The government later announced a strategic partnership with Telesat and MDA Space and a first $2.92M engineering/options-analysis contract.

Positioning implication: lead with resilient communications dependency analysis, multi-provider evidence, link/service provenance, and sovereign data governance. Do not say ContinuityOS provides MILSATCOM, secures CAF communications, or integrates with Telesat/MDA.

### Arctic surveillance and domain awareness

Canada's 2025 A-OTHR announcement describes selected transmit/receive sites, a four-site eventual capability, anticipated initial operational capability in 2029, and its relationship to Northern Approaches surveillance and NORAD modernization.

Positioning implication: ContinuityOS can support an unclassified readiness/exercise evidence layer around dependencies such as power, backhaul, weather, maintenance, logistics, and alternate routes. It must not process or infer radar tracks, threat identities, classified warning, or NORAD decisions.

### Polar maritime infrastructure

The 2025 $3.25B Canadian Coast Guard polar icebreaker contract under the National Shipbuilding Strategy connects Arctic sovereignty/security with navigation, science, environmental protection, emergency response, and Indigenous/community support. The announcement references the Canada-US-Finland ICE Pact.

Positioning implication: model the Arctic as a civil-military-adjacent continuity ecosystem rather than a weapons-only problem: ice services, ports, fuel, vessels, communications, search-and-rescue, communities, weather, environmental constraints, and supply corridors.

### Shared Services Canada satellite situational-awareness services

A 2025 Shared Services Canada solicitation sought satellite communication and situational-awareness, tracking, and messaging value-added services on an as-and-when-required basis for a three-year term plus options. A later CanadaBuys notice states the subsequent RFP cancelled/superseded the prior solicitation.

Positioning implication: monitor procurement notices and build a source-qualified procurement intelligence feed, but do not infer award, buyer intent, or incumbent weakness from a tender notice alone.

### Polar OTHR contracting

CanadaBuys records a 2025 Polar Over-the-Horizon Radar Phase 4 award notice involving Atco Frontec Ltd. and Inuvialuit Development Corporation in joint venture, with DND as contracting organization.

Positioning implication: demonstrate respect for Indigenous participation, land claims, local capacity, environmental assessment, and northern logistics. A credible product must not treat northern infrastructure as an abstract empty map.

## System landscape and non-claims

| Adjacent system/category | Publicly visible strength | ContinuityOS role | Do not claim |
|---|---|---|---|
| Palantir Foundry/AIP | Integrated data/ontology/workflow platform and defence contracts | Smaller, inspectable, sovereignty-oriented continuity evidence layer | Palantir replacement, equivalent scale, classified capability |
| Esri | Mature GIS, geospatial analytics, public-sector ecosystem | Open-source/OGC/STAC evidence and dependency analysis that can export to GIS | Replacement for enterprise GIS or official mapping |
| Databricks | Lakehouse, ML, governance and large-scale analytics | Small-reference temporal analytics and governed model artifacts | Equivalent distributed lakehouse performance |
| Government operational systems | Authority, sensors, procedures, accredited boundaries | External evidence companion/pilot layer | Authority to override official systems |
| NATO data-centric architecture | Federated data spaces, originator control, metadata, ABAC/zero trust, interoperability | Design target for open contracts and policy boundaries | NATO interoperability, access, endorsement, or compliance |
| EU regulated operators | Risk management, logging, documentation, human oversight, cybersecurity, incident governance | Evidence/traceability support component | Automatic AI Act/NIS2/DORA/GDPR compliance |

## Contract-ready capability language

Use:

- "unclassified pilot"
- "customer-controlled deployment option"
- "open-standard data ingestion boundary"
- "evidence lineage and replay"
- "scenario analysis with temporal holdout"
- "human approval and accountable operator workflow"
- "tenant isolation target; currently not customer-ready multi-tenant"
- "supports continuity planning; does not exercise operational authority"

Avoid:

- "operational intelligence"
- "real-time NORAD picture"
- "AI-powered national security command"
- "battlefield decision superiority"
- "predicts adversary intent"
- "classified-ready"
- "NATO/Five Eyes interoperable"
- "replaces Palantir"

## Public procurement readiness package

Before approaching a Canadian public-sector, critical-infrastructure, or allied buyer, maintain:

1. One-page capability statement with exact boundary and target users.
2. Architecture diagram showing tenant boundary, data classes, sources, keys, audit trail, and human gates.
3. Public-data source register with licence, API/key status, rate limits, retention, and stale-data behavior.
4. Threat model covering data poisoning, spoofed telemetry, supply-chain compromise, insider misuse, cross-tenant leakage, model drift, and availability failure.
5. Security control mapping to NIST CSF 2.0, ISO/IEC 27001/27701, and customer-required Canadian controls; label this as a mapping, not certification.
6. Privacy impact and data-residency assessment.
7. SBOM, reproducible build evidence, signed release hashes, vulnerability process, and incident response runbook.
8. Pilot evaluation protocol with labelled outcomes, false-positive/false-negative measures, human override rate, latency, stale-data rate, and rollback.
9. Indigenous/community engagement and northern operating-context plan where relevant.
10. Procurement, insurance, liability, export-control, and accreditation review by qualified professionals.

## Strategic differentiation

The serious differentiation is not model size. It is controlled evidence:

- public and customer data remain distinguishable;
- every derived conclusion has source and time lineage;
- every tenant can retain control of its data;
- the system can run offline from signed snapshots;
- uncertainty and missingness are visible;
- models are evaluated on temporal holdouts rather than only fitting historical data;
- human authority remains explicit;
- outputs are exportable in open formats;
- deployment can be Canadian-controlled and later federated without pretending federation already exists.
