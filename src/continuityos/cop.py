"""Common Operating Picture (COP) Symbology & Military Standard Exporter.

Maps ContinuityOS corridor operational states to Mil-Std-2525D / NATO APP-6D
symbology and exports GeoJSON COP feature collections with defense overlays.
"""

from __future__ import annotations

from typing import Any

from continuityos.domain import CorridorAssessment, CorridorState

# Mil-Std-2525D / APP-6D Symbol Identification Codes (SIDC)
# Standard structure: Version(10) + StandardIdentity(03=Friend, 04=Neutral)
# + SymbolSet(30=Maritime) + EntityType + ...
_MIL_STD_2525_SIDCS: dict[CorridorState, dict[str, str]] = {
    CorridorState.OPEN: {
        "sidc": "10033000001201000000",
        "symbol_name": "Maritime Transit Lane - Operational (Friend/Green)",
        "condition": "Fully Capable",
        "color": "#00FF00",
    },
    CorridorState.OPEN_DEGRADED: {
        "sidc": "10033000001202000000",
        "symbol_name": "Maritime Transit Lane - Degraded (Yellow)",
        "condition": "Damaged / Degraded",
        "color": "#FFFF00",
    },
    CorridorState.OPEN_CAPACITY_CONSTRAINED: {
        "sidc": "10033000001203000000",
        "symbol_name": "Maritime Transit Lane - Capacity Constrained (Yellow/Amber)",
        "condition": "Throughput Constrained",
        "color": "#FFA500",
    },
    CorridorState.OPEN_BUT_UNINSURABLE: {
        "sidc": "10043000001204000000",
        "symbol_name": "Maritime Transit Lane - Uninsurable (Orange)",
        "condition": "Commercial Failure",
        "color": "#FF8C00",
    },
    CorridorState.OPEN_BUT_NO_CARRIER_CAPACITY: {
        "sidc": "10043000001205000000",
        "symbol_name": "Maritime Transit Lane - Carrier Diverted (Orange)",
        "condition": "Logistics Abandoned",
        "color": "#FF7F50",
    },
    CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED: {
        "sidc": "10043000001206000000",
        "symbol_name": "Maritime Transit Lane - PNT/GNSS Spoofed (Purple/Red)",
        "condition": "Navigation Denied",
        "color": "#800080",
    },
    CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED: {
        "sidc": "10043000001207000000",
        "symbol_name": "Maritime Transit Lane - SATCOM Denied (Blue/Red)",
        "condition": "Communications Severed",
        "color": "#4682B4",
    },
    CorridorState.FUNCTIONALLY_CLOSED: {
        "sidc": "10063000001208000000",
        "symbol_name": "Maritime Transit Lane - Functionally Closed (Red)",
        "condition": "Impassable / Denied",
        "color": "#FF0000",
    },
    CorridorState.PHYSICALLY_CLOSED: {
        "sidc": "10063000001209000000",
        "symbol_name": "Maritime Transit Lane - Physically Blocked (Dark Red)",
        "condition": "Destroyed / Impassable",
        "color": "#8B0000",
    },
}


def export_cop_feature(
    corridor_id: str,
    assessment: CorridorAssessment,
    coordinates: list[list[float]] | None = None,
    security_banner: str = "UNCLASSIFIED",
) -> dict[str, Any]:
    """Export a single corridor assessment as a Mil-Std-2525 GeoJSON feature."""
    state_enum = CorridorState.from_str(assessment.state)
    symbology = _MIL_STD_2525_SIDCS.get(
        state_enum,
        {
            "sidc": "10043000000000000000",
            "symbol_name": "Unknown Corridor Condition",
            "condition": "Unknown",
            "color": "#808080",
        },
    )

    geometry: dict[str, Any]
    if coordinates:
        geometry = {"type": "LineString", "coordinates": coordinates}
    else:
        # Default placeholder Arctic corridor geometry if unsupplied
        geometry = {
            "type": "LineString",
            "coordinates": [[33.08, 68.95], [40.0, 70.0], [60.0, 75.0], [72.07, 71.27]],
        }

    return {
        "type": "Feature",
        "id": corridor_id,
        "geometry": geometry,
        "properties": {
            "corridor_id": corridor_id,
            "corridor_state": state_enum.value,
            "overall_risk": assessment.overall_risk,
            "confidence": assessment.confidence,
            "mil_std_2525_sidc": symbology["sidc"],
            "mil_std_2525_name": symbology["symbol_name"],
            "operational_condition": symbology["condition"],
            "map_color": symbology["color"],
            "security_classification_banner": security_banner,
            "factors": [f.model_dump(mode="json") for f in assessment.factors],
            "caveats": assessment.caveats,
        },
    }


def export_cop_feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap COP features in a standard GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "properties": {
            "title": "ContinuityOS Defense Common Operating Picture (COP) Layer",
            "symbology_standard": "MIL-STD-2525D / NATO APP-6D",
            "generated_by": "ContinuityOS Sovereign Defense Suite",
        },
        "features": features,
    }
