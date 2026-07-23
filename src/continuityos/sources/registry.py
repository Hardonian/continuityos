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
