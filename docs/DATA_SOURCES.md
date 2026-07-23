# Open and Public Data Sources

The data plane separates **context** from **live operational truth**. Public datasets are valuable, but many cannot legitimately establish current service availability, cyber health, port capacity, insurance access, or asset readiness.

| Source | Implemented use | Explicitly prohibited inference |
|---|---|---|
| NOAA@NSIDC Sea Ice Index v4 | 1981–2010 day-of-year extent anomaly and historical climate context | Safe local navigation, vessel-specific accessibility, live escort requirement |
| ECCC MSC GeoMet OGC API | Weather, climate, water, and selected Canadian ice products after collection-specific mapping | Port availability or cyber condition |
| Copernicus CDSE Sentinel-1 STAC | Discover all-weather/day-night radar imagery metadata | Automatic claim that an object or event exists without validated image processing |
| ECMWF Open Data | Forecast inputs with model-run and forecast-step provenance | Certainty about future route conditions |
| CelesTrak GP | Orbital geometry and catalogue context | Starlink or any provider's live coverage, capacity, latency, authorization, or availability |
| NGA World Port Index | Port coordinates and published characteristics | Live berth, fuel, labour, security, or cargo-handling availability |
| MarineCadastre.gov AIS | Historical U.S. vessel traffic observations | Complete vessel presence, identity integrity, or global Arctic coverage |
| UN Comtrade | Reported trade exposure and commodity concentration | Current shipment status or physical inventory |
| OpenStreetMap, if added | Basemap and volunteered geographic context | Authoritative infrastructure status |
| Authenticated operator telemetry | Live scoped capacity, availability, cyber health, inventory, insurance, and escort assertions | State outside the signed tenant, asset, and freshness scope |
| Structured analyst assessment | Geopolitical context, policy judgment, scenarios, confidence | Automated assertion of adversary intent as fact |

## Implemented endpoints and references

- NSIDC daily northern extent CSV: `https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv`
- ECCC GeoMet OGC API: `https://api.weather.gc.ca/`
- Copernicus STAC: `https://stac.dataspace.copernicus.eu/v1/`
- ECMWF open forecasts: `https://data.ecmwf.int/forecasts/`
- CelesTrak GP: `https://celestrak.org/NORAD/elements/gp.php`
- NGA WPI: `https://msi.nga.mil/Publications/WPI`
- MarineCadastre AIS: `https://marinecadastre.gov/ais/`
- UN Comtrade: `https://comtradeapi.un.org/`

## Snapshot requirements

Climate, Earth-observation catalogue coverage, orbital geometry, and static port geometry are marked **context-only** and cannot reduce a live operability score.

Every external payload used in an assessment should retain:

- source identifier;
- exact URI or canonical request;
- retrieval timestamp;
- response content hash;
- ETag or last-modified value when available;
- licence and attribution;
- parser and transform version;
- spatial and temporal validity;
- confidence and known limitations.

## Navigation warning

The reference implementation is not a navigation system. Sea-ice extent, satellite imagery, weather models, and port maps require qualified operational interpretation and cannot replace official charts, notices, ice services, pilots, or vessel-specific decisions.
