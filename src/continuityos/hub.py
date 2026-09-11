"""Global Corridor Hub Client & Pre-Modeled Chokepoint Registry.

Provides turn-key access to verified, pre-modeled global strategic corridors:
- Strait of Malacca
- Suez Canal & Red Sea Bab-el-Mandeb
- Panama Canal
- Strait of Hormuz
- Taiwan Strait
- Baltic Sea & Danish Straits
- Rhine-Alpine Inland Corridor
- Canadian Arctic Northwest Passage / Ring of Fire
"""

from __future__ import annotations

from pydantic import BaseModel

from continuityos.domain import CorridorState


class GlobalChokepointModel(BaseModel):
    """Declarative specification of a verified global strategic transit corridor."""

    corridor_id: str
    name: str
    category: str  # MARITIME_CHOKEPOINT, INLAND_WATERWAY, STRATEGIC_MINERALS, ENERGY_CANAL
    region: str
    latitude: float
    longitude: float
    annual_tonnage_millions: float
    primary_threat_vector: str
    nominal_transit_days: float
    alternate_route_id: str
    alternate_transit_days: float
    current_effective_state: CorridorState = CorridorState.OPEN
    resilience_rating: str = "A"


GLOBAL_CORRIDOR_CATALOG: dict[str, GlobalChokepointModel] = {
    "malacca-strait": GlobalChokepointModel(
        corridor_id="corridor/malacca-strait",
        name="Strait of Malacca",
        category="MARITIME_CHOKEPOINT",
        region="Southeast Asia",
        latitude=2.5000,
        longitude=101.5000,
        annual_tonnage_millions=1200.0,
        primary_threat_vector="Congestion, Piracy & Naval Chokepoint Interdiction",
        nominal_transit_days=3.0,
        alternate_route_id="corridor/sunda-lombok-bypass",
        alternate_transit_days=6.5,
        resilience_rating="A",
    ),
    "suez-red-sea": GlobalChokepointModel(
        corridor_id="corridor/suez-red-sea",
        name="Suez Canal & Bab-el-Mandeb",
        category="MARITIME_CHOKEPOINT",
        region="Middle East / Red Sea",
        latitude=29.9700,
        longitude=32.5500,
        annual_tonnage_millions=1000.0,
        primary_threat_vector="Drone/Missile Anti-Ship Strikes & War-Risk Underwriter Withdrawal",
        nominal_transit_days=4.0,
        alternate_route_id="corridor/cape-of-good-hope-bypass",
        alternate_transit_days=16.0,
        resilience_rating="BBB",
    ),
    "panama-canal": GlobalChokepointModel(
        corridor_id="corridor/panama-canal",
        name="Panama Canal Locks",
        category="MARITIME_CHOKEPOINT",
        region="Central America",
        latitude=9.0800,
        longitude=-79.6800,
        annual_tonnage_millions=510.0,
        primary_threat_vector="Gatun Lake Freshwater Drought & Vessel Draft Restrictions",
        nominal_transit_days=2.0,
        alternate_route_id="corridor/us-intermodal-rail-landbridge",
        alternate_transit_days=7.0,
        resilience_rating="A",
    ),
    "hormuz-strait": GlobalChokepointModel(
        corridor_id="corridor/hormuz-strait",
        name="Strait of Hormuz",
        category="ENERGY_CANAL",
        region="Persian Gulf",
        latitude=26.5600,
        longitude=56.2500,
        annual_tonnage_millions=950.0,
        primary_threat_vector="Petroleum Tanker Seizures, Mines & GNSS EW Spoofing",
        nominal_transit_days=2.0,
        alternate_route_id="corridor/east-west-crude-pipeline",
        alternate_transit_days=5.0,
        resilience_rating="BBB",
    ),
    "taiwan-strait": GlobalChokepointModel(
        corridor_id="corridor/taiwan-strait",
        name="Taiwan Strait Advanced Semiconductor Corridor",
        category="STRATEGIC_MINERALS",
        region="East Asia",
        latitude=24.0000,
        longitude=119.5000,
        annual_tonnage_millions=750.0,
        primary_threat_vector="Airspace Denial, Maritime Blockades & Foundry Logistics Severance",
        nominal_transit_days=3.0,
        alternate_route_id="corridor/luzon-east-philippine-bypass",
        alternate_transit_days=5.5,
        resilience_rating="BB",
    ),
    "baltic-danish-straits": GlobalChokepointModel(
        corridor_id="corridor/baltic-danish-straits",
        name="Baltic Sea & Danish Straits",
        category="MARITIME_CHOKEPOINT",
        region="Northern Europe",
        latitude=55.5000,
        longitude=11.0000,
        annual_tonnage_millions=420.0,
        primary_threat_vector="Subsea Fiber Cuts, Dark Fleet Collisions & GPS Jamming",
        nominal_transit_days=3.0,
        alternate_route_id="corridor/kiel-canal-rail-corridor",
        alternate_transit_days=4.5,
        resilience_rating="AA",
    ),
    "rhine-alpine": GlobalChokepointModel(
        corridor_id="corridor/rhine-alpine",
        name="Rhine-Alpine Inland Heavy Freight Corridor",
        category="INLAND_WATERWAY",
        region="Western Europe",
        latitude=50.1500,
        longitude=7.6500,
        annual_tonnage_millions=300.0,
        primary_threat_vector="Kaub Gauge Low-Water Barge Groundings & Rail Bottlenecks",
        nominal_transit_days=4.0,
        alternate_route_id="corridor/betuwe-heavy-rail-freight",
        alternate_transit_days=3.5,
        resilience_rating="AA",
    ),
    "arctic-northwest-passage": GlobalChokepointModel(
        corridor_id="corridor/arctic-northwest-passage",
        name="Canadian Arctic Northwest Passage & Ring of Fire",
        category="STRATEGIC_MINERALS",
        region="North America (Arctic)",
        latitude=74.0000,
        longitude=-95.0000,
        annual_tonnage_millions=45.0,
        primary_threat_vector="Multi-Year Sea-Ice Obstruction, Polar Night & Zero SATCOM",
        nominal_transit_days=18.0,
        alternate_route_id="corridor/trans-canada-all-weather-rail",
        alternate_transit_days=8.0,
        resilience_rating="A",
    ),
}


class CorridorHubClient:
    """Registry client for searching, inspecting, and pulling pre-modeled global corridors."""

    @staticmethod
    def list_corridors(category: str | None = None) -> list[GlobalChokepointModel]:
        """Return all catalog corridors, optionally filtered by category."""
        if category:
            return [c for c in GLOBAL_CORRIDOR_CATALOG.values() if c.category == category]
        return list(GLOBAL_CORRIDOR_CATALOG.values())

    @staticmethod
    def pull_corridor(corridor_id: str) -> GlobalChokepointModel | None:
        """Fetch an individual corridor model by ID or slug."""
        clean_id = corridor_id.replace("corridor/", "")
        return GLOBAL_CORRIDOR_CATALOG.get(clean_id)
