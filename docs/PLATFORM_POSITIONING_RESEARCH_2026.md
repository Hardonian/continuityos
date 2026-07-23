# ContinuityOS positioning research

**As of:** 2026-07-23  
**Scope:** serious alternatives/adjacent systems and standards for a Canadian/EU-compatible governed continuity data platform.  
**Evidence convention:** “Verified” means stated in a current public product document, legal document, regulation, or standards body publication. Vendor capability descriptions are still vendor claims; they are not independent assurance or proof that every deployment/configuration has the capability.

## Executive conclusion

ContinuityOS should not position itself as “a sovereign Palantir,” a replacement for a GIS, lakehouse, SIEM, or a legal compliance program. The credible wedge is narrower and more defensible:

> **A governed continuity data plane for organizations that need to preserve operational context, provenance, authority, and recoverability across tenants, jurisdictions, vendors, and degraded connectivity—using open exchange formats and explicit human accountability.**

The strongest differentiation is the combination, not any single feature:

1. **Jurisdiction- and tenant-explicit control:** policy objects state where data may reside/process, who may administer it, what subprocessors are allowed, and which tenant boundary applies. “Canada/EU-compatible” should mean configurable controls and evidence, not a blanket legal conclusion.
2. **Continuity as a first-class object:** versioned situation/state snapshots, dependencies, RTO/RPO, recovery tests, export/restore packages, degraded/offline operation, and evidence that a restore actually worked.
3. **Provenance plus authority:** every material fact, transformation, inference, recommendation, and action has source, time, confidence, lineage, policy basis, and accountable human/role. AI may recommend; it does not silently become the authority.
4. **Open, inspectable interchange:** DCAT-AP metadata, OGC APIs/GeoPackage for geospatial data, STIX/TAXII for cyber threat data, documented JSON/CSV/Parquet exports, and signed manifests. Avoid a proprietary ontology as the only exit path.
5. **Evidence-oriented contracts:** a DPA, subprocessor register, residency/processing matrix, incident notice, audit evidence, deletion/return, exit assistance, and continuity schedule that map to actual controls and tests.

These are not empty spaces: Palantir and Databricks already have strong lineage, access control, auditability, AI governance, and provenance claims; Esri already has self-hosted/disconnected GIS; NATO’s current public strategy explicitly calls for federated data meshes, national sovereignty, data products, metadata catalogues, and interoperability-by-design. ContinuityOS wins only if it makes **continuity evidence, tenant isolation, cross-jurisdiction control, human authority, and portable exit** the product’s center of gravity.

## Positioning matrix

| Alternative / adjacent system | Verified public capability or pattern | Where it is strong | What ContinuityOS can credibly differentiate on | Do not claim |
|---|---|---|---|---|
| **Palantir Foundry + AIP + Apollo** | Foundry/AIP publicly describe ontology-based data/logic/action/security, role/marking/purpose controls, provenance, audit logs, agent observability, human+AI workflows, and packaging/deployment across heterogeneous environments. Palantir also publicly describes Dedicated Foundry/Gotham, disconnected/classified deployments, data-residency/isolation options, and customer legal ownership. Public GCP terms show a product license/order form plus incorporated DPA; the terms also reference U.S. trade controls. | Deep operational model, granular security, AI/action integration, deployment engineering, government/mission credibility. | Be **smaller, inspectable, portable, and continuity-first**: tenant-specific cryptographic boundaries; jurisdiction policy as a machine-checkable object; signed snapshot/restore evidence; explicit authority ledger; open exports and standards profiles; no requirement to adopt a proprietary ontology. | “Palantir cannot do sovereignty,” “Foundry lacks provenance/human controls,” or “ContinuityOS has the same mission scale.” These are false or unsupported. Also do not imply Palantir’s marketing descriptions are independent certification. |
| **Esri ArcGIS Enterprise / ArcGIS Online** | ArcGIS Enterprise is self-hosted on customer infrastructure, supports on-prem/cloud/Kubernetes, disconnected operation, access control, update control, backup/DR, and geospatial management. Esri publishes hardening guidance recommending centralized identity, publication review, classification, staging/production isolation, and tested backup/restore. Esri’s DPA identifies customer as controller and Esri as processor/subprocessor for relevant services and includes SCCs. | Best-in-class geospatial data, map/feature workflows, field/disconnected use, mature deployment choices. | Position as the **governed cross-system continuity layer around GIS**, not as another GIS: preserve non-GIS operational facts, decisions, dependencies, authority, and restore evidence; use OGC APIs/GeoPackage and link to ArcGIS rather than replace it. | “Esri is cloud-only,” “Esri cannot run disconnected,” or “ContinuityOS replaces ArcGIS.” |
| **Databricks + Unity Catalog** | Unity Catalog publicly documents centralized access control, row/column policies, lineage, audit logs, classification, data quality monitoring, sharing, and AI governance. Databricks’ MCSA says customer retains rights in Customer Content; the public DPA covers processor roles, subprocessors, SCCs, legal requests, breach notice, audit reports, deletion, and explicitly says the services do not include backup/DR for Customer Personal Data. | Lakehouse analytics/ML scale, catalog and lineage, open-source Unity Catalog direction, broad data/AI tooling. | Provide **operational continuity and governance evidence**, not just lakehouse governance: recovery package + tested restore; tenant/jurisdiction isolation; authority and decision provenance; cross-vendor/event/geospatial/CTI interchange. | “Databricks provides DR by default” (its public DPA says the opposite for Customer Personal Data); “Unity Catalog makes the whole estate portable”; or “lineage automatically covers arbitrary external systems.” |
| **NATO data/interoperability direction** | NATO’s 2025 Data Strategy and 2026 Alliance Digital Strategy call for an Alliance Data Sharing Ecosystem, federated data meshes/data spaces, catalogues of catalogues, common metadata, data products, interoperability-by-design, controlled sharing, Zero Trust, federated identity, and preservation of national data sovereignty/autonomy/accountability. The public DCRA v2 is federated, domain-centric, data-product based and identifies federated catalogues as critical. | Strongest reference model for federated, multinational, mission and degraded-environment governance. | Use the **same architectural vocabulary at a non-classified commercial/public-sector level**: domain ownership, data products, federated catalogue, labels, need-to-know, policy-bound exchange, human authority, continuity across disconnected/degraded conditions. | “NATO-certified,” “NATO interoperable,” “FMN compliant,” or “approved for classified use” without an actual authorization, profile conformance, or procurement basis. NATO strategy is not a product certification. |
| **EU AI Act** | Regulation (EU) 2024/1689’s high-risk section includes data governance, technical documentation, record keeping, transparency, human oversight, accuracy/robustness/cybersecurity; Article 16 describes provider duties including QMS, documentation, logs, conformity assessment, corrective actions, and authority cooperation. Applicability depends on system role, use case, and classification. | Defines a regulatory target for AI accountability and evidence. | Ship an **AI evidence/control plane**: model/system inventory, intended purpose, risk classification, data provenance, evals, human oversight, logs, incident/corrective-action workflow, exportable technical file. | “AI Act compliant” globally; “ContinuityOS is high-risk compliant” without a use-case assessment, QMS, conformity route, and legal review; or claim every continuity workflow is an AI system. |
| **NIS2 / ENISA implementation guidance** | NIS2 broadens critical-sector scope and raises cybersecurity/risk/reporting expectations. ENISA’s current guidance for covered digital infrastructure/ICT providers maps to Commission Implementing Regulation 2024/2690 and includes risk management, incident handling, business continuity/crisis management, supply chain, secure development, cryptography, access control, asset management, and physical/environmental security. | Concrete EU cyber-resilience and continuity expectations, especially for providers and critical entities. | Make continuity controls **operational and evidenced**: dependency inventory, RTO/RPO, restore tests, incident timelines, supplier obligations, exception/risk acceptance, management reporting, and post-termination controls. | “NIS2 certified” (NIS2 is not a generic product certification); “NIS2 applies to every customer”; or “a dashboard equals compliance.” |
| **DORA** | DORA (EU) 2022/2554 is a financial-sector regulation consolidating ICT risk management, incident reporting, resilience testing, and ICT third-party risk. Its recitals and operative framework emphasize contractual safeguards and critical/important functions. | High-value pattern for contracts, exit, resilience testing, audit/access, incident cooperation, and third-party concentration risk. | Offer a **DORA-ready evidence and contract pack** for financial customers: service criticality, subcontractor map, data locations, audit/evidence rights, incident SLA, continuity/exit testing, deletion/return, portability, and concentration-risk facts. | “DORA compliant” without customer scope and legal assessment; or imply that a platform can satisfy the financial entity’s governance duties by itself. |
| **ISO/IEC 27001:2022** | ISMS requirements; risk-based, organization-wide management system. Certification is optional and must be by an accredited conformity assessment body. | Baseline security governance and assurance language. | Map each ContinuityOS control/evidence item to ISO clauses/Annex A in a customer-facing matrix and maintain an auditable control register. | “ISO 27001 certified” unless currently certified; “ISO compliance” as a product feature independent of organizational scope. |
| **ISO/IEC 27701:2025** | Current ISO page identifies a published 2025 PIMS standard for PII controllers and processors, independently usable and aligned with ISO/IEC 27001. | Privacy accountability, processor/controller evidence, PII lifecycle. | Native processing inventory, purpose/legal-basis metadata, minimization, retention/deletion proof, subject-request assistance, transfer/subprocessor records, and privacy control mapping. | “GDPR certified” or “27701 compliant” without a scoped PIMS and evidence. |
| **ISO/IEC 42001:2023** | AIMS management-system standard for organizations developing/providing/using AI; addresses risks/opportunities and continual improvement rather than certifying an individual model’s outputs. | Responsible AI governance at organizational level. | Treat every AI-assisted decision/action as a governed object with intended purpose, owner, human authority, evals, incident/remediation, and change history. | “42001 certifies our model” or “42001 guarantees fair/accurate AI.” |
| **NIST CSF 2.0** | Outcome-based framework with a new Govern function and explicit supply-chain category GV.SC. It does not prescribe one implementation. | Common buyer language for governance, risk, suppliers, and improvement. | Publish a ContinuityOS CSF 2.0 profile and evidence export, especially GV.OC/GV.RR/GV.OV/GV.SC, plus Identify/Protect/Detect/Respond/Recover mappings. | “NIST certified” or “CSF 2.0 compliance” as a binary product status. |
| **STIX 2.1 / TAXII 2.1** | OASIS STIX expresses cyber threat/observable information; TAXII defines REST resources and requirements for exchanging CTI, designed for STIX. | Cyber threat exchange and SOC/CERT interoperability. | Native optional CTI connectors, preserve source markings/confidence/timestamps, sign/verify packages, and link CTI objects to continuity incidents and recovery decisions. | “STIX/TAXII makes all continuity data interoperable”; these standards are CTI-focused, not a general governance model. |
| **OGC API Features / GeoPackage** | OGC API Features provides modular OpenAPI building blocks for web feature access. GeoPackage 1.4 is an open, platform-independent SQLite-based format for vector/raster/tabular geospatial data, useful in limited connectivity. | Geospatial exchange and offline/edge portability. | Adopt OGC API Features and GeoPackage for spatial snapshots, offline bundles, and field exchange; attach ContinuityOS provenance, authority, tenant, and policy metadata without corrupting the standard payload. | “OGC compliant” without conformance testing; or present GeoPackage as a full enterprise GIS replacement. |
| **DCAT / DCAT-AP** | DCAT is a catalogue vocabulary; EU Publications Office states DCAT-AP is the application profile for European data portals and adds domain constraints. | Cross-catalogue discovery and machine-readable metadata. | Export a federated continuity catalogue using DCAT-AP-compatible dataset/distribution metadata plus jurisdiction, classification, retention, provenance, quality, and access-policy extensions. | “DCAT-AP proves lawful access” or “a catalogue is the data.” |
| **Gaia-X** | Public Gaia-X Compliance Document 24.06 emphasizes openness, transparency, data protection, security, portability, European control, contractual framework, verifiable credentials, trust anchors, and conformity assessment. It supports self-declaration and CAB-backed evidence at different levels. | Useful vocabulary and evidence model for European control, portability, and verifiable claims. | Implement a **Gaia-X-aligned evidence profile** where useful: signed service/tenant/residency/subprocessor claims, machine-readable service description, portability/exit facts, and verifiable evidence links. | “Gaia-X certified” or “European sovereign” merely because the platform runs in Europe; Gaia-X conformance is profile/release/evidence-specific and evolving. |
| **Canadian public-sector sovereignty guidance** | Government of Canada materials distinguish residency from sovereignty: Canadian storage does not by itself remove foreign-law access risk. The GC digital-sovereignty framework includes legal, security, privacy, workforce, supply-chain, resilience, integrity, and institutional control; it notes contracts need access/disclosure/continuity controls. | Important Canadian buyer reality: jurisdiction of provider/operators and operational control matter alongside physical location. | Provide a transparent sovereignty factsheet: legal entity/operator jurisdictions, support/admin access, subprocessors, key custody, data/metadata/log locations, cross-border flows, compelled-access process, exit, and continuity. Offer Canada-hosted/customer-hosted deployment profiles. | “Data in Canada = sovereign,” “PIPEDA compliant” as a platform-wide claim, or claim a Canadian region defeats foreign legal exposure. |

## What ContinuityOS should claim (with evidence)

Use claims that can be tested in a demo, contract, or evidence export:

- **“Tenant-isolated by design”** only if isolation is explicit in the architecture and tested: separate tenant identifiers, authorization checks, storage prefixes/buckets/databases, encryption/key boundaries, caches, queues, logs, backups, exports, and support tooling. Publish negative tests for cross-tenant reads, writes, searches, exports, and restore.
- **“Residency and processing-policy aware”** if every asset has declared allowed locations and every connector/job/admin path is checked and logged against policy. State the exact profile (e.g., customer-hosted Canada; EU region; Canadian operator) rather than generic sovereignty.
- **“Provenance-preserving”** if source, timestamp, transformation, version, confidence, actor/agent, policy basis, and hash/signature survive ingestion, derivation, export, and restore. Define coverage and known blind spots.
- **“Human-authorized continuity decisions”** if authority is a first-class field and the system blocks or escalates high-impact actions until an authorized role approves. Record delegation, expiry, justification, dissent/override, and final disposition.
- **“Open standards-based exchange”** if the product passes conformance tests and publishes schemas/profiles. Say “supports DCAT-AP metadata, OGC API Features/GeoPackage, STIX/TAXII” rather than “fully interoperable.”
- **“Continuity evidence, not just backups”** if the platform produces signed recovery packages, RTO/RPO definitions, restore-test results, dependency snapshots, and a customer-readable chain of evidence.
- **“Supports GDPR/NIS2/DORA/AI Act/ISO/NIST control mapping”** if it provides mappings and evidence exports. Say the customer remains responsible for scope, legal interpretation, governance, and certification.

## What not to claim

1. **No blanket “sovereign” claim.** Residency, legal jurisdiction, operator nationality, support access, key custody, and subprocessor control are different dimensions. Use a sovereignty/residency matrix.
2. **No “compliant by deployment.”** Regulations and management-system standards are scope- and organization-dependent. Use “supports,” “maps to,” “evidence-ready,” or “customer-configurable.”
3. **No “zero trust” badge without a model and tests.** Show identity, device/service authorization, least privilege, segmentation, continuous evaluation, logging, and policy enforcement.
4. **No “air-gapped” claim unless the actual product, update path, support path, telemetry, and dependency set work without network access.** Disconnected operation is a deployment profile, not a slogan.
5. **No “unbreakable,” “tamper-proof,” “complete lineage,” or “guaranteed recovery.”** Use cryptographic integrity, append-only/immutable controls where actually implemented, lineage coverage percentages, and tested recovery objectives.
6. **No implication that human-in-the-loop alone satisfies EU AI Act human oversight.** Oversight must be meaningful, competent, timely, and able to interpret/override the system in context.
7. **No NATO/defence authorization implication.** “Aligned with public NATO data-centric principles” is materially different from NATO approval, FMN conformance, or classified accreditation.
8. **No claim that open standards eliminate vendor lock-in.** Export formats, semantics, licenses, proprietary extensions, operational runbooks, and migration tooling all matter.
9. **No “customer owns everything” shortcut.** Contracts must distinguish customer data/content, derived artifacts, platform IP, models, logs, telemetry, support data, and aggregate analytics.
10. **No silent AI authority.** Recommendations, automated actions, model/version, input data, confidence, policy, and approving human must be visible and exportable.

## Concrete product requirements

### P0 — trust boundary and tenancy

- Tenant identity is mandatory on every API, object, event, job, cache key, queue message, log, backup, snapshot, export, and admin action.
- Default-deny authorization with tenant, role, attribute, purpose, temporal, classification, jurisdiction, and action scopes.
- Separate customer data, metadata, audit logs, backups, and encryption keys at least logically; provide physically/dedicated profiles for high-assurance customers.
- Customer-controlled SSO (OIDC/SAML), SCIM, MFA, service identities, break-glass workflow, JIT elevation, admin session recording, and dual control for exports/deletion/key changes.
- Automated cross-tenant isolation tests in CI and pre-release, including search/index/embedding leakage and restore-to-wrong-tenant tests.

### P0 — provenance, authority, and policy

- Canonical event envelope: `tenant_id`, `asset_id`, `event_id`, `source`, `source_version`, `observed_at`, `recorded_at`, `actor`, `agent/model`, `transformation`, `confidence`, `classification`, `purpose`, `jurisdiction`, `policy_decision`, `authority`, `approval`, `hash`, and `parent_event_ids`.
- Append-only or tamper-evident audit ledger with export and independent verification; synchronized time assumptions documented.
- Human authority registry: role, scope, delegation, expiry, conflict-of-interest/segregation-of-duties, approval evidence, override, dissent, and revocation.
- Policy decision point that evaluates residency, purpose, classification, tenant, retention, export, and subprocessor constraints before action—not only after logging it.
- AI register and evidence: model/provider/version, allowed data, prompt/tool policy, evaluations, human oversight, output disposition, incident/correction, and rollback.

### P0 — continuity and recovery

- Continuity object model: service, capability, dependency, owner, criticality, RTO, RPO, maximum tolerable outage, manual fallback, contact, jurisdiction, data classification, and last-tested date.
- Versioned snapshots of data, metadata, policy, identity/authority, schemas, connectors, model references, and dependency manifests.
- Signed export/restore bundles with manifest, hashes, schema version, encryption/key instructions, tenant, residency, retention, and authority metadata.
- Restore to clean environment with automated verification; record RTO/RPO results, missing dependencies, exceptions, and approver.
- Customer-controlled backup retention/deletion and a documented exit process; do not promise DR unless the service contract includes it.
- Offline/degraded mode for priority functions, including conflict resolution and reconciliation after reconnect.

### P1 — open standards and interoperability

- DCAT-AP-compatible catalogue export; document local extensions and SHACL/JSON Schema validation.
- OGC API Features and GeoPackage profiles for geospatial continuity assets.
- STIX/TAXII 2.1 connectors for cyber incidents/threat intelligence; preserve markings, confidence, object IDs, and source provenance.
- Human-readable and machine-readable exports: JSON, CSV, Parquet, signed manifest, and documented API/OpenAPI; no proprietary-only export.
- Mapping layer for customer ontologies and NATO-like domain/data-product concepts without claiming NATO conformance.
- Optional Gaia-X-style verifiable service/tenant/residency claims, with issuer, evidence URL/hash, validity, and revocation.

### P1 — compliance/evidence product

- Control mappings: ISO/IEC 27001:2022, ISO/IEC 27701:2025, ISO/IEC 42001:2023, NIST CSF 2.0, GDPR Articles 28/32, NIS2/2024-2690 themes, DORA ICT-third-party themes, and customer-specific controls.
- Evidence register with owner, control, artifact, timestamp, scope, test result, exception, risk acceptance, and expiry.
- Subprocessor inventory and change notice workflow; data-flow/residency map; legal-request and breach workflow.
- DPA/contract annex generator with controller/processor roles, instructions, confidentiality, security measures, audit evidence, incident timing, transfers/SCCs, deletion/return, exit support, and continuity commitments.
- Customer portal that exports a regulator/auditor package without exposing other tenants.

### P1 — measurable assurance

Publish a capability matrix with “implemented / configurable / roadmap / not supported,” and attach proof:

- isolation test report;
- restore drill report;
- export/import round-trip test;
- OGC/DCAT/STIX/TAXII conformance tests;
- access/export/deletion audit samples;
- model and human-approval trace;
- residency/subprocessor factsheet;
- uptime, RTO/RPO, backup scope, and support-access commitments.

## Contract patterns worth adopting

The public documents reviewed show a repeatable enterprise pattern, regardless of vendor:

1. **Master agreement + order form/service schedule + DPA/security addendum.** Keep product scope, service levels, data roles, security measures, subprocessors, and jurisdiction in separable schedules.
2. **Customer content ownership and platform IP separation.** Databricks’ public MCSA is a clear example of this structure; Palantir public terms similarly separate licensed software/materials from customer use, and Esri uses a master agreement plus product-specific terms.
3. **Processor instructions and transfer mechanism.** GDPR Article 28 requires processor contracts to define subject matter, duration, nature/purpose, data/categories, instructions, confidentiality, subprocessing, assistance, deletion/return, and audits. Use SCCs where required; do not rely on a marketing privacy page.
4. **Subprocessor notice/objection.** Maintain a versioned list, notice period, objection route, replacement/termination remedy, and evidence of flow-down obligations.
5. **Government-access process.** Contract for prompt notice where lawful, redirection to the customer, minimization, challenge/protective-order cooperation, transparency reports where available, and a documented conflict-of-law path.
6. **Operational resilience schedule.** Define critical services, RTO/RPO, backup/restore scope, test cadence, incident notice, recovery communications, dependencies, planned maintenance, and customer participation.
7. **Exit and portability schedule.** Define formats, metadata/provenance preservation, keys, retention/deletion certificates, assistance period, fees, read-only transition, and proof of successful import into a customer-controlled environment.
8. **Assurance/evidence schedule.** List current certifications/attestations by scope and period, audit report access, penetration-test summary, vulnerability disclosure, control exceptions, and customer audit limits.

## Source register (authoritative/current public sources)

### Vendors and commercial contracts

- Palantir, [AIP architecture](https://palantir.com/docs/foundry/architecture-center/aip-architecture/); [data protection and governance](https://palantir.com/docs/foundry/security/data-protection-and-governance/); [2025 Form 10-K](https://investors.palantir.com/files/2025%20FY%20PLTR%2010-K.pdf); [public GCP terms](https://www.palantir.com/assets/xrfr7uokpv1b/2ajxcAAipDS2EAkFxZZvDa/ed556b05d8ef5d80b91a0e7bf8aff559/Palantir_Terms_and_Conditions_for_GCP.pdf); [Dedicated/disconnected deployment context](https://blog.palantir.com/a-sky-full-of-clouds-218b9db3f735).
- Esri, [ArcGIS Enterprise](https://www.esri.com/en-us/arcgis/products/arcgis-enterprise/overview); [hardening guide](https://content.esri.com/resources/enterprisegis/arcgis_enterprise_hardening_guide.pdf); [DPA](https://www.esri.com/content/dam/esrisites/en-us/media/legal/gdpr-data-processing-addendums/data-process-addend.pdf); [master agreements](https://www.esri.com/en-us/legal/terms/master-agreement).
- Databricks, [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/); [MCSA](https://www.databricks.com/legal/mcsa); [DPA](https://www.databricks.com/sites/default/files/legal/dpa-20230721.pdf).

### Law, public-sector guidance, and standards

- NATO, [Data Strategy for the Alliance (2025)](https://www.nato.int/en/about-us/official-texts-and-resources/official-texts/2025/05/05/data-strategy-for-the-alliance); [Alliance Digital Strategy (2026)](https://www.nato.int/en/about-us/official-texts-and-resources/official-texts/2026/01/13/alliance-digital-strategy); [DCRA v2](https://nhqc3s.hq.nato.int/apps/public/AC322-D(2025)0056-Data_Centric_Reference_Architecture_v2.pdf).
- EU AI Act, [Article 16 and related high-risk provisions](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-16); [GDPR Article 28/current EUR-Lex text](https://eur-lex.europa.eu/eli/reg/2016/679/art_28/oj); [DORA Regulation 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj); [ENISA NIS2 technical guidance](https://www.enisa.europa.eu/publications/nis2-technical-implementation-guidance).
- ISO, [ISO/IEC 27001:2022](https://www.iso.org/standard/27001); [ISO/IEC 27701:2025](https://www.iso.org/standard/27701); [ISO/IEC 42001:2023](https://www.iso.org/standard/42001).
- NIST, [CSF 2.0](https://csrc.nist.gov/pubs/cswp/29/the-nist-cybersecurity-framework-csf-20/final); [CSF 2.0 supply-chain guide](https://csrc.nist.gov/pubs/sp/1305/final).
- OASIS, [STIX 2.1](https://www.oasis-open.org/standard/6426/); [TAXII 2.1](https://www.oasis-open.org/standard/taxii-version-2-1/).
- OGC, [GeoPackage](https://www.ogc.org/standards/geopackage/); [OGC API Features](https://www.ogc.org/standards/ogcapi-features/).
- EU Publications Office, [application profiles / DCAT-AP](https://op.europa.eu/en/web/eu-vocabularies/application-profiles).
- Gaia-X, [Compliance Document 24.06](https://docs.gaia-x.eu/policy-rules-committee/compliance-document/24.06/pdf/document.pdf).
- Government of Canada, [Digital sovereignty framework](https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/cloud-services/digital-sovereignty/digital-sovereignty-framework-improve-digital-readiness.html); [data sovereignty/public cloud white paper](https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/cloud-services/digital-sovereignty/gc-white-paper-data-sovereignty-public-cloud.html); [privacy in contracting guidance](https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/privacy/guidance-document-taking-privacy-into-account-before-making-contracting-decisions.html).

## Research limits

- Public vendor pages establish publicly stated capabilities and contract patterns, not the security posture of an individual customer deployment.
- No private Palantir, Esri, Databricks, NATO, or customer procurement documents were reviewed. Palantir’s public terms and 10-K are useful evidence of public contractual/product language, but they do not establish every Foundry/AIP commercial term.
- Regulatory applicability is fact-specific and changes with implementation guidance, delegated acts, national transposition, sector, role, and use case. This report is positioning/product guidance, not legal advice.
