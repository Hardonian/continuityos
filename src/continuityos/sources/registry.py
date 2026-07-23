from __future__ import annotations

from dataclasses import dataclass

from continuityos.domain import AssertionClass, SourceTrust


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    source_id: str
    name: str
    base_url: str
    trust: SourceTrust
    allowed_assertions: frozenset[AssertionClass]
    licence: str
    notes: str
    access: str = "public_http"
    api_key_required: bool = False
    cadence: str = "source-defined"


SOURCES: dict[str, SourceDefinition] = {
    "nsidc-sea-ice-index": SourceDefinition(
        source_id="nsidc-sea-ice-index",
        name="NOAA@NSIDC Sea Ice Index v4",
        base_url="https://noaadata.apps.nsidc.org/NOAA/G02135/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.CLIMATE, AssertionClass.ICE}),
        licence="US government data; verify dataset terms and attribution",
        notes="Climate and sea-ice context only; not a navigation product.",
    ),
    "eccc-geomet": SourceDefinition(
        source_id="eccc-geomet",
        name="Meteorological Service of Canada GeoMet OGC API",
        base_url="https://api.weather.gc.ca/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset(
            {AssertionClass.CLIMATE, AssertionClass.ICE, AssertionClass.WEATHER}
        ),
        licence="Government of Canada Open Government Licence",
        notes="Use product-specific metadata and validity windows.",
    ),
    "copernicus-cdse-stac": SourceDefinition(
        source_id="copernicus-cdse-stac",
        name="Copernicus Data Space Ecosystem STAC",
        base_url="https://stac.dataspace.copernicus.eu/v1/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset(
            {AssertionClass.EARTH_OBSERVATION, AssertionClass.GEOLOCATION}
        ),
        licence="Copernicus data terms; product-specific attribution required",
        notes="Imagery metadata is evidence context; derived claims require validated processing.",
    ),
    "ecmwf-open-data": SourceDefinition(
        source_id="ecmwf-open-data",
        name="ECMWF Open Data",
        base_url="https://data.ecmwf.int/forecasts/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.WEATHER, AssertionClass.CLIMATE}),
        licence="CC BY 4.0 for open catalogue products",
        notes="GRIB decoding is optional and must preserve model run and step metadata.",
    ),
    "celestrak-gp": SourceDefinition(
        source_id="celestrak-gp",
        name="CelesTrak General Perturbations Data",
        base_url="https://celestrak.org/NORAD/elements/gp.php",
        trust=SourceTrust.OPEN_CONTEXT,
        allowed_assertions=frozenset({AssertionClass.ORBITAL_GEOMETRY}),
        licence="CelesTrak usage policy",
        notes="Orbital elements do not prove communications service availability or capacity.",
    ),
    "nga-world-port-index": SourceDefinition(
        source_id="nga-world-port-index",
        name="NGA World Port Index",
        base_url="https://msi.nga.mil/Publications/WPI",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.GEOLOCATION}),
        licence="US public-domain source data",
        notes=(
            "Port presence and published characteristics do not prove current "
            "capacity or availability."
        ),
    ),
    "marinecadastre-ais": SourceDefinition(
        source_id="marinecadastre-ais",
        name="MarineCadastre.gov AIS",
        base_url="https://marinecadastre.gov/ais/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.TRAFFIC_HISTORY}),
        licence="US government data; dataset-specific terms",
        notes="Historical AIS has coverage, reception, spoofing and reporting limitations.",
    ),
    "un-comtrade": SourceDefinition(
        source_id="un-comtrade",
        name="United Nations Comtrade",
        base_url="https://comtradeapi.un.org/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.TRADE_EXPOSURE}),
        licence="UN Comtrade terms of use",
        notes="Trade exposure is reported data and may lag current operational conditions.",
    ),
    "statcan-wds": SourceDefinition(
        source_id="statcan-wds",
        name="Statistics Canada Web Data Service / SDMX",
        base_url="https://www.statcan.gc.ca/en/developers/wds",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.TRADE_EXPOSURE, AssertionClass.CLIMATE}),
        licence="Statistics Canada terms and Open Government Licence where applicable",
        notes=(
            "Business-day statistical releases; preserve table/vector metadata and reporting lag."
        ),
        cadence="business-day releases",
    ),
    "noaa-coops": SourceDefinition(
        source_id="noaa-coops",
        name="NOAA CO-OPS water levels, tides, currents and meteorology",
        base_url="https://api.tidesandcurrents.noaa.gov/api/prod/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.WEATHER, AssertionClass.CLIMATE}),
        licence="NOAA public data; product-specific attribution and datum requirements",
        notes=(
            "Water-level observations and predictions require station, datum, product and "
            "verification metadata."
        ),
        cadence="minute-to-daily products",
    ),
    "usgs-water": SourceDefinition(
        source_id="usgs-water",
        name="USGS Water Data OGC APIs",
        base_url="https://api.waterdata.usgs.gov/ogcapi/v0/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.CLIMATE, AssertionClass.WEATHER}),
        licence="USGS public data; API terms and source attribution",
        notes=(
            "Keyless low-volume access is possible; higher limits use a free api.data.gov "
            "key. Some OGC services are alpha."
        ),
        api_key_required=False,
        cadence="continuous and daily collections",
    ),
    "nasa-firms": SourceDefinition(
        source_id="nasa-firms",
        name="NASA FIRMS active fire observations",
        base_url="https://firms.modaps.eosdis.nasa.gov/api/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.EARTH_OBSERVATION, AssertionClass.CLIMATE}),
        licence="NASA FIRMS terms; free MAP_KEY required",
        notes=(
            "Fire hotspots are alerts/context and require coverage, confidence and "
            "field/authority corroboration."
        ),
        api_key_required=True,
        cadence="near-real-time and historical",
    ),
    "noaa-swpc": SourceDefinition(
        source_id="noaa-swpc",
        name="NOAA Space Weather Prediction Center public products",
        base_url="https://www.swpc.noaa.gov/products/",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.WEATHER, AssertionClass.CLIMATE}),
        licence="NOAA public products; product-specific terms",
        notes="Space-weather context only; does not prove a satellite or communications outage.",
        cadence="near-real-time products and forecasts",
    ),
    "gdacs": SourceDefinition(
        source_id="gdacs",
        name="Global Disaster Alert and Coordination System API",
        base_url="https://www.gdacs.org/gdacsapi/swagger/index.html",
        trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        allowed_assertions=frozenset({AssertionClass.CLIMATE, AssertionClass.GEOLOCATION}),
        licence="GDACS public API terms",
        notes=(
            "Disaster alerts are machine-readable context and not a substitute for local "
            "authority confirmation."
        ),
        cadence="event-driven",
    ),
    "reliefweb": SourceDefinition(
        source_id="reliefweb",
        name="UN OCHA ReliefWeb API",
        base_url="https://api.reliefweb.int/v2/",
        trust=SourceTrust.OPEN_CONTEXT,
        allowed_assertions=frozenset(
            {AssertionClass.POLICY_CONTEXT, AssertionClass.GEOPOLITICAL_CONTEXT}
        ),
        licence="ReliefWeb API terms; read-only public archive",
        notes="Curated humanitarian reporting; preserve publisher, date, and editorial context.",
        cadence="continuously updated archive",
    ),
    "openalex": SourceDefinition(
        source_id="openalex",
        name="OpenAlex scholarly metadata API",
        base_url="https://api.openalex.org/",
        trust=SourceTrust.OPEN_CONTEXT,
        allowed_assertions=frozenset({AssertionClass.POLICY_CONTEXT}),
        licence="OpenAlex terms and source-level licences",
        notes="Evidence discovery and literature traceability, not operational validation.",
        cadence="continuously updated metadata",
    ),
    "operator-telemetry": SourceDefinition(
        source_id="operator-telemetry",
        name="Authenticated operator telemetry",
        base_url="internal://operator-telemetry",
        trust=SourceTrust.AUTHENTICATED_OPERATOR,
        allowed_assertions=frozenset(
            {
                AssertionClass.LIVE_CAPACITY,
                AssertionClass.LIVE_AVAILABILITY,
                AssertionClass.CYBER_HEALTH,
                AssertionClass.INSURANCE_ACCESS,
            }
        ),
        licence="Customer-controlled",
        notes=(
            "Must be authenticated, scoped, freshness-checked and retained under customer policy."
        ),
    ),
    "analyst-assessment": SourceDefinition(
        source_id="analyst-assessment",
        name="Structured analyst assessment",
        base_url="internal://analyst-assessment",
        trust=SourceTrust.ANALYST_ASSESSMENT,
        allowed_assertions=frozenset(
            {
                AssertionClass.GEOPOLITICAL_CONTEXT,
                AssertionClass.POLICY_CONTEXT,
                AssertionClass.HUMAN_INTELLIGENCE,
            }
        ),
        licence="Customer-controlled",
        notes="Must distinguish observed facts, analytic judgments and scenarios.",
    ),
}


def get_source(source_id: str) -> SourceDefinition:
    try:
        return SOURCES[source_id]
    except KeyError as exc:
        raise ValueError(f"unknown source_id: {source_id}") from exc
