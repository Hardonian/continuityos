# Public Data Terms and Control Map

Status: evidence-backed implementation note, not legal advice or legal approval.

Evidence retrieval date: 2026-07-23 EDT.

## Purpose

This document separates verified provider terms from ContinuityOS implementation controls. A source being technically accessible does not mean every commercial redistribution, retention, derivative product, or operational use is permitted.

## Verified sources

| Source | Official endpoint/resource | Verified terms | ContinuityOS treatment |
|---|---|---|---|
| ECCC MSC GeoMet weather alerts | https://api.weather.gc.ca/collections/weather-alerts/items?f=json&limit=100 | GeoMet identifies ECCC/MSC as the provider and links to Government of Canada terms. ECCC's meteorological-data terms permit use/customization and redistribution subject to attribution and passing terms to recipients; the service/data are provided as-is and continuity is not guaranteed. | `eccc-geomet-alerts`; outbound disabled by default; snapshot URL/hash/retrieval time retained; alert expiry, geometry, confidence, impact, and provider attribution retained; never treated as an operational forecast or government endorsement. |
| DFO/CHS IWLS | https://api-iwls.dfo-mpo.gc.ca/swagger-ui/index.html | CHS licence states the data are not for navigation, commercial derivative products for sale/profit are prohibited under that licence, copyright remains with CHS, metadata must be considered, copies must be destroyed within 15 days after termination, and the prescribed non-navigation/non-endorsement notice applies to derivative products. | `dfo-iwls`; usable for controlled research/evidence integration only until a commercial-use permission is confirmed; source-native units and QC/review state retained; no navigation, route control, or commercial derivative-water-level product claim. |
| Canadian Disaster Database | https://open.canada.ca/data/en/dataset/1c3d15f9-9cfa-4010-8462-0d67e493d9b9 | Public Safety Canada lists the dataset under the Open Government Licence - Canada. The CDD page warns that it aggregates outside sources, may include third-party licensing/copyright restrictions, is not a primary source, may be unsuitable for comparative analysis, and recent values may be preliminary/incomplete. | `canadian-disaster-database`; XLSX snapshot parser; historical event/context only; every normalized indicator receives `aggregated_secondary_source` and `not_primary_source`; no automatic operational label or causal claim. |
| Open Government Licence - Canada 2.0 | https://open.canada.ca/en/open-government-licence-canada | Permits lawful commercial and non-commercial reuse, subject to attribution and exclusions for personal information, third-party rights, official marks, and other rights not licensed by the provider. It does not grant endorsement or official-status rights and is provided as-is. | Attribution and provider-specific restrictions remain metadata; source-specific restrictions override generic OGL assumptions; legal review gate remains open. |
| Copernicus Data Space Ecosystem | https://dataspace.copernicus.eu/terms-and-conditions | Sentinel data are described as free/full/open under the Sentinel legal notice. Other portal content is stated to be non-commercial, with no general right to resell/redistribute portal content. User accounts, quotas, service availability limits, and EU data-processing locations are documented. | STAC metadata is catalogue/context unless the exact product licence is recorded; no bulk acquisition or portal-content redistribution without product-level terms and quota review. |
| NOAA/NWS public information | https://www.weather.gov/disclaimer | NWS pages generally state information is public domain unless specifically noted, but prohibit claiming ownership, implying endorsement/affiliation, or modifying content and presenting it as official government material. | Preserve source/date/time; no endorsement language; product-specific notices still checked before redistribution. |
| GDACS | https://www.gdacs.org/About/termofuse.aspx | GDACS describes model-generated, partly automatic notifications and impact estimates, provided as-is and requiring validation against authoritative sources before decision use. | Contextual alert only; preserve model/uncertainty warning; never use as sole operational authority or label without independent confirmation. |

## Controls implemented

- Explicit allow-listed source IDs.
- Outbound HTTP disabled by default in the service.
- Operator probes require `--enable-outbound`.
- Exact request URLs are cache keys, including encoded query parameters.
- Immutable content-addressed payloads use SHA-256 hashes.
- Snapshot metadata preserves URL, retrieval time, status, content type, ETag/Last-Modified when supplied, and source ID.
- Normalized indicators preserve source snapshot IDs, timestamps, native units, quality flags, station/event identity, and source-specific limitations.
- Protected indicator routes require the ContinuityOS API key.
- CDD indicators are explicitly marked aggregated/secondary/non-primary.
- DFO indicators preserve the CHS non-navigation restriction in documentation and are not exposed as navigation output.
- No credentials, API keys, or customer data are stored in source snapshots or repository files.

## Open human/legal gates

- Confirm the exact commercial redistribution/use rights for DFO/CHS data before selling a derived product or including it in a customer-facing commercial deliverable.
- Check product-level Sentinel/third-party terms for every Copernicus product, not just STAC metadata.
- Review retention, deletion-on-termination, attribution, privacy, cross-border transfer, and customer contract language with qualified counsel.
- Confirm each customer-supplied telemetry licence and purpose limitation.
- Obtain customer approval for any labelled outcome dataset and retain its provenance/authorization record.

## Truthful classification

These sources are lawful public-data candidates and tested technical inputs. They are not evidence of government endorsement, institutional selection, operational authority, classified access, or continuous production connectivity.
