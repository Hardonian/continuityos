# Public Data Acquisition Catalog (2025-current)

Status: lawful public-data integration plan, not a claim that every source is production-connected
Reviewed: 2026-07-23

## Operating rule

ContinuityOS uses public data for bounded observations and context. It never promotes public context into live service availability, cyber health, capacity, military readiness, or intent without an authenticated and authorized source that is allowed to make that assertion.

All ingestors must store: canonical request, retrieval time, response hash, source terms/licence, parser version, spatial/temporal validity, quality flags, and rate-limit state. Outbound access is opt-in.

## Priority sources

| Domain | Source/API | Access | Key status | Cadence/shape | Intended use | Hard limit |
|---|---|---|---|---|---|---|
| Canada weather/ice/water | ECCC MSC GeoMet OGC API, https://api.weather.gc.ca/ | REST/OGC | No key for public endpoints; verify rate/terms | Forecasts, observations, geospatial products | Weather, ice, climate, water observations | Not live port/cyber/capacity truth |
| Canada statistics/trade/economy | Statistics Canada WDS/SDMX, https://www.statcan.gc.ca/en/developers/wds | REST/SDMX | Keyless public service | Business-day updates; JSON/CSV/SDMX | Labour, demographics, trade/economic indicators | Reporting lag; rate limits; not real-time logistics |
| Global trade | UN Comtrade, https://comtradeapi.un.org/ | REST | Guest access and registered tiers; verify current quota | Monthly/annual reported trade | Commodity/country concentration and exposure | Not shipment position or inventory |
| Sea ice | NOAA@NSIDC Sea Ice Index, https://noaadata.apps.nsidc.org/NOAA/G02135/ | CSV | Keyless | Daily historical index | Climate/ice context and anomaly features | Not route clearance or vessel safety |
| Water/tides | NOAA CO-OPS, https://api.tidesandcurrents.noaa.gov/api/prod/ | REST | Keyless examples; identify application and limits | 6-min, hourly, daily, predictions | Water level, currents, tides, flood context | US/Gt Lakes station coverage; datum and verification matter |
| Water | USGS Water Data APIs, https://api.waterdata.usgs.gov/docs/ | OGC/REST | Keyless low-volume; free api.data.gov key for higher limits | Continuous/daily/metadata | River/groundwater/water condition features | New OGC APIs may be alpha; not Canadian coverage |
| EO catalogue | Copernicus CDSE STAC, https://stac.dataspace.copernicus.eu/v1/ | STAC REST | Catalogue metadata public; imagery access/product terms vary | Spatiotemporal items | Sentinel discovery, cloud/coverage/observation context | Metadata is not a validated event detection |
| EO fire | NASA FIRMS, https://firms.modaps.eosdis.nasa.gov/api/ | REST/WMS/WFS | Free MAP_KEY via https://firms.modaps.eosdis.nasa.gov/api/map_key/ | Near-real-time/historical hotspots | Wildfire and thermal anomaly context | Key, quotas, false positives, satellite coverage |
| Weather models | ECMWF Open Data, https://data.ecmwf.int/forecasts/ | Registry/files | Public open products; terms vary | Model runs/forecast steps | Ensemble/forecast features | Forecast uncertainty and licence must remain attached |
| Space weather | NOAA SWPC, https://www.swpc.noaa.gov/products/ | JSON/RSS/feeds | Public feeds; check product terms | Near-real-time products | Solar/geomagnetic disruption context | No direct claim of satellite/telecom outage |
| Disasters | GDACS API, https://www.gdacs.org/gdacsapi/swagger/index.html | REST/GeoJSON | Keyless | Event alerts | Earthquake, cyclone, flood, volcano context | Alert products are not ground truth |
| Humanitarian events | ReliefWeb API, https://apidoc.reliefweb.int/ | REST | Keyless read-only with appname | Continuously updated archive | Curated reports/disaster context | Editorial/coverage bias; no attribution of intent |
| Historical vessel traffic | MarineCadastre AIS, https://marinecadastre.gov/ais/ | Files/services | Public US dataset; terms vary | Historical AIS | Traffic baselines and route patterns | Reception, spoofing, identity and geographic limits |
| Port geography | NGA World Port Index, https://msi.nga.mil/Publications/WPI | Download/publication | Public source; verify terms | Periodic/static | Port geolocation and published characteristics | Never infer current berth, labour, fuel or security status |
| Orbital context | CelesTrak GP, https://celestrak.org/NORAD/elements/gp.php | JSON/TLE | Public access subject to policy | Frequently updated catalogue | Orbital geometry/context | Does not prove Starlink service, coverage, capacity or authorization |
| Open geospatial context | OGC APIs and OpenStreetMap, https://www.opengeospatial.org/ and https://www.openstreetmap.org/ | REST/files | Terms vary; OSM ODbL obligations | Variable | Basemap and volunteered context | Not authoritative infrastructure status |
| Open-source news/context | GDELT, https://www.gdeltproject.org/ | Public APIs/files | Terms and quotas apply | Near-real-time event/media metadata | Discovery and corroboration queue | Not intelligence, attribution, or fact without source review |
| Academic evidence | Crossref, OpenAlex, arXiv, https://api.openalex.org/ and https://export.arxiv.org/api/query | REST/OAI | Public; rate/terms apply | Publication metadata | Evidence discovery and literature traceability | Academic publication is not operational validation |

## API-key acquisition plan

1. Start keyless and cache aggressively.
2. Use a dedicated organization-owned mailbox and named service identity for NASA FIRMS and USGS api.data.gov keys.
3. Store keys only in protected runtime configuration; never commit them, put them in URLs, or include them in evidence payloads.
4. Record provider terms, quota, expiration, and rotation owner in the source registry.
5. Fail soft to cached data with an explicit stale-data status; never silently substitute another source.

## Data-plane expansion order

1. Canada: ECCC GeoMet + Statistics Canada WDS/SDMX.
2. Arctic/environment: NSIDC + ECMWF + NOAA SWPC + Copernicus STAC.
3. Water/port: Canadian gauges where available, NOAA CO-OPS for relevant cross-border/Gt Lakes corridors, USGS for watershed context.
4. Hazards: GDACS + NASA FIRMS + ReliefWeb.
5. Trade/logistics: UN Comtrade + MarineCadastre AIS + port reference data.
6. Academic and open-source context: OpenAlex/Crossref/arXiv + GDELT only as discovery/context.
7. Customer-controlled telemetry: capacity, service status, cyber health, inventory, carrier/port operating state, insurer access, and authorized incident data.

## Source authority matrix

| Claim | Public context permitted | Stronger source required |
|---|---|---|
| Sea ice/climate/weather/water observation | Yes, within product validity | Official operational service for safety decisions |
| Satellite/orbital geometry | Yes | Provider/ground telemetry for availability/capacity |
| Historic traffic pattern | Yes | Authenticated/current AIS and operator verification |
| Trade dependency | Yes | Customer inventory, contracts, shipment and supplier data |
| Fire/flood/disaster alert | Yes, labelled alert | Local authority/field confirmation |
| Port location/characteristics | Yes | Port operator telemetry and official notices |
| Cyber health/service availability | No | Signed tenant-scoped operator telemetry or monitoring evidence |
| Military/NORAD/NATO state | No | Authorized official source; ContinuityOS must not infer it |
| Adversary intent | No | Human analytic judgment with documented sourcing and review |

## Licensing and privacy

Every source adapter must retain attribution and terms. Personal data, vessel-personal identifiers, customer telemetry, and sensitive infrastructure details require purpose limitation, minimization, retention, access control, tenant isolation, and jurisdiction review. Public availability does not eliminate privacy, contractual, security, export-control, or sovereignty obligations.
