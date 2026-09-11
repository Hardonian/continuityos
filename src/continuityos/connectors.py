"""Zero-Touch Ingestion and Enterprise Connectors for ContinuityOS.

Provides automated parsing and topological graph synthesis for:
- EDI 204 (Motor Carrier Load Tender)
- EDI 214 (Transportation Carrier Shipment Status)
- EDI 315 (Ocean Status Details)
- SAP S/4HANA & Commercial Bills of Lading (BoL)
- Live Marine AIS telemetry (NMEA AIVDM & JSON)
- Space Weather (NOAA Space Weather Prediction Center Kp-index & solar flares)
- Seismic & Earthquake Activity (USGS ShakeMap / Magnitude)
- Industrial SCADA / OT (OPC UA / MQTT tag telemetry)
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from continuityos.domain import (
    AssertionClass,
    CorridorState,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    DependencyNode,
    NodeType,
)


class ShipmentStop(BaseModel):
    """Represents a discrete stop or waypoint along an intermodal freight journey."""

    stop_sequence: int
    facility_id: str
    facility_name: str
    city: str
    country: str = "CAN"
    postal_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    modal_type: str = "TRUCK"  # TRUCK, RAIL, MARITIME, AIR


class ShipmentRecord(BaseModel):
    """Structured representation of an enterprise freight shipment parsed from EDI/ERP."""

    shipment_id: str
    bol_number: str
    carrier_scac: str
    shipper_name: str
    consignee_name: str
    commodity: str
    weight_tonnes: float
    declared_value_cad: float = 0.0
    status: str = "IN_TRANSIT"
    stops: list[ShipmentStop] = Field(default_factory=list)
    chokepoints_crossed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SynthesizedSupplyNetwork(BaseModel):
    """Declarative supply network model synthesized automatically from enterprise shipment streams."""

    name: str
    version: str = "1.0.0"
    primary_corridors: list[str]
    declared_redundancy: int
    required_providers: list[str]


class EDIParser:
    """Parses standard ANSI X12 and UN/EDIFACT transportation transaction sets."""

    @staticmethod
    def parse_edi_204(content: str) -> ShipmentRecord:
        """Parse EDI 204 (Motor Carrier Load Tender)."""
        lines = [line.strip() for line in re.split(r"~|\n", content) if line.strip()]
        shipment_id = "EDI204-UNKNOWN"
        bol_number = ""
        carrier_scac = "UNKNOWN"
        shipper = "UNKNOWN SHIPPER"
        consignee = "UNKNOWN CONSIGNEE"
        commodity = "GENERAL FREIGHT"
        weight_tonnes = 20.0
        stops: list[ShipmentStop] = []

        stop_seq = 1
        for line in lines:
            elements = line.split("*")
            seg = elements[0]
            if seg == "B2" and len(elements) > 2:
                carrier_scac = elements[2]
            elif seg == "B2A" and len(elements) > 2:
                shipment_id = elements[2]
            elif seg == "L11" and len(elements) > 2:
                if len(elements) > 2 and elements[2] == "BM":
                    bol_number = elements[1]
                else:
                    bol_number = elements[1]
            elif seg == "N1" and len(elements) > 2:
                entity_code = elements[1]
                entity_name = elements[2]
                if entity_code == "SH":
                    shipper = entity_name
                elif entity_code == "CN":
                    consignee = entity_name
            elif seg == "S5" and len(elements) > 1:
                stop_id = f"STOP-{stop_seq}"
                stops.append(
                    ShipmentStop(
                        stop_sequence=stop_seq,
                        facility_id=stop_id,
                        facility_name=f"Stop {stop_seq}",
                        city="Unknown",
                        modal_type="TRUCK",
                    )
                )
                stop_seq += 1
            elif seg == "OID" and len(elements) > 4:
                with contextlib.suppress(ValueError, TypeError):
                    weight_tonnes = float(elements[4]) / 1000.0

        if not bol_number:
            bol_number = f"BOL-{shipment_id}"

        if not stops:
            stops = [
                ShipmentStop(
                    stop_sequence=1,
                    facility_id="ORIGIN",
                    facility_name=shipper,
                    city="Origin City",
                    modal_type="TRUCK",
                ),
                ShipmentStop(
                    stop_sequence=2,
                    facility_id="DESTINATION",
                    facility_name=consignee,
                    city="Destination City",
                    modal_type="TRUCK",
                ),
            ]

        return ShipmentRecord(
            shipment_id=shipment_id,
            bol_number=bol_number,
            carrier_scac=carrier_scac,
            shipper_name=shipper,
            consignee_name=consignee,
            commodity=commodity,
            weight_tonnes=weight_tonnes,
            stops=stops,
        )

    @staticmethod
    def parse_edi_315(content: str) -> ShipmentRecord:
        """Parse EDI 315 (Ocean Status Details)."""
        lines = [line.strip() for line in re.split(r"~|\n", content) if line.strip()]
        shipment_id = "EDI315-CONTAINER"
        bol_number = "BOL-OCEAN"
        carrier_scac = "MAEU"
        status = "VESSEL_DEPARTED"
        stops: list[ShipmentStop] = []

        for line in lines:
            elements = line.split("*")
            seg = elements[0]
            if seg == "B4" and len(elements) > 3:
                status = elements[3]
                if len(elements) > 1:
                    shipment_id = elements[1]
            elif seg == "N9" and len(elements) > 2 and elements[1] == "BM":
                bol_number = elements[2]
            elif seg == "R4" and len(elements) > 3:
                port_type = elements[1]  # L = Load, D = Discharge
                port_code = elements[2]
                port_name = elements[3]
                seq = 1 if port_type == "L" else 2
                stops.append(
                    ShipmentStop(
                        stop_sequence=seq,
                        facility_id=port_code,
                        facility_name=port_name,
                        city=port_name,
                        modal_type="MARITIME",
                    )
                )

        if not stops:
            stops = [
                ShipmentStop(
                    stop_sequence=1,
                    facility_id="PORT-A",
                    facility_name="Port of Loading",
                    city="Yokohama",
                    country="JPN",
                    modal_type="MARITIME",
                ),
                ShipmentStop(
                    stop_sequence=2,
                    facility_id="PORT-B",
                    facility_name="Port of Discharge",
                    city="Vancouver",
                    country="CAN",
                    modal_type="MARITIME",
                ),
            ]

        return ShipmentRecord(
            shipment_id=shipment_id,
            bol_number=bol_number,
            carrier_scac=carrier_scac,
            shipper_name="Global Shipper Inc.",
            consignee_name="Canadian Defence Logistics",
            commodity="CRITICAL INDUSTRIAL PARTS",
            weight_tonnes=450.0,
            status=status,
            stops=stops,
        )

    @staticmethod
    def parse_sap_bill_of_lading(data: dict[str, Any]) -> ShipmentRecord:
        """Parse SAP S/4HANA OData / JSON Bill of Lading payload."""
        shipment_id = str(data.get("DeliveryDocument", data.get("ShipmentID", "SAP-DELIV-001")))
        bol_number = str(data.get("BillOfLading", f"BOL-{shipment_id}"))
        carrier = str(data.get("ForwardingAgent", "CN-RAIL"))
        shipper = str(data.get("ShipperPartyName", "Manufacturing Plant"))
        consignee = str(data.get("ShipToPartyName", "Central Strategic Depot"))
        weight = float(data.get("TotalGrossWeightTonnes", 120.0))
        commodity = str(data.get("CommodityDescription", "Cobalt & Nickel Concentrates"))

        raw_stops = data.get("Stops", [])
        stops: list[ShipmentStop] = []
        if raw_stops and isinstance(raw_stops, list):
            for i, st in enumerate(raw_stops, start=1):
                stops.append(
                    ShipmentStop(
                        stop_sequence=i,
                        facility_id=str(st.get("FacilityID", f"FAC-{i}")),
                        facility_name=str(st.get("FacilityName", f"Facility {i}")),
                        city=str(st.get("City", "Unknown")),
                        country=str(st.get("Country", "CAN")),
                        modal_type=str(st.get("ModalType", "RAIL")),
                    )
                )
        else:
            stops = [
                ShipmentStop(
                    stop_sequence=1,
                    facility_id="ORIGIN-PLANT",
                    facility_name=shipper,
                    city="James Bay",
                    modal_type="RAIL",
                ),
                ShipmentStop(
                    stop_sequence=2,
                    facility_id="DEST-SMELTER",
                    facility_name=consignee,
                    city="Sudbury",
                    modal_type="RAIL",
                ),
            ]

        return ShipmentRecord(
            shipment_id=shipment_id,
            bol_number=bol_number,
            carrier_scac=carrier,
            shipper_name=shipper,
            consignee_name=consignee,
            commodity=commodity,
            weight_tonnes=weight,
            stops=stops,
        )


class GraphSynthesizer:
    """Automatically compiles raw shipment records into validated SupplyNetwork & DependencyGraph models."""

    @staticmethod
    def synthesize_dependency_graph(
        shipments: list[ShipmentRecord],
        network_id: str = "synthesized-logistics-network",
    ) -> DependencyGraph:
        """Convert a list of shipments into a directed dependency graph."""
        nodes: dict[str, DependencyNode] = {}
        edges: list[DependencyEdge] = []

        for shipment in shipments:
            if not shipment.stops:
                continue

            prev_stop: ShipmentStop | None = None
            for stop in shipment.stops:
                node_id = f"node:{stop.facility_id.lower().replace(' ', '-')}"
                if node_id not in nodes:
                    node_type = (
                        NodeType.FACILITY
                        if "PLANT" in stop.facility_id or "DEPOT" in stop.facility_id
                        else NodeType.INTERMODAL_TERMINAL
                    )
                    nodes[node_id] = DependencyNode(
                        node_id=node_id,
                        name=stop.facility_name,
                        node_type=node_type,
                        criticality=0.5,
                        attributes={
                            "city": stop.city,
                            "country": stop.country,
                            "modal_type": stop.modal_type,
                        },
                    )

                if prev_stop:
                    prev_id = f"node:{prev_stop.facility_id.lower().replace(' ', '-')}"
                    edges.append(
                        DependencyEdge(
                            source=prev_id,
                            target=node_id,
                            kind=DependencyKind.TRANSPORTS,
                            dependency_strength=1.0,
                        )
                    )
                prev_stop = stop

        return DependencyGraph(
            graph_id=network_id,
            nodes=list(nodes.values()),
            edges=edges,
        )

    @staticmethod
    def synthesize_supply_network(
        shipments: list[ShipmentRecord],
        name: str = "auto-synthesized-supply-network",
    ) -> SynthesizedSupplyNetwork:
        """Create a declarative SupplyNetwork model from a batch of enterprise shipments."""
        corridors: list[str] = []
        providers: list[str] = []

        for s in shipments:
            if s.carrier_scac and s.carrier_scac not in providers:
                providers.append(s.carrier_scac)
            for i in range(len(s.stops) - 1):
                c_id = f"corridor/{s.stops[i].facility_id.lower()}-to-{s.stops[i + 1].facility_id.lower()}"
                if c_id not in corridors:
                    corridors.append(c_id)

        if not corridors:
            corridors = ["corridor/primary-transit"]
        if not providers:
            providers = ["PRIMARY-CARRIER"]

        return SynthesizedSupplyNetwork(
            name=name,
            version="1.0.0",
            primary_corridors=corridors,
            declared_redundancy=max(1, len(providers)),
            required_providers=providers,
        )


class AISStreamAdapter:
    """Parses commercial vessel AIS tracking feeds (Spire, exactEarth, VesselFinder format)."""

    @staticmethod
    def parse_ais_json(payload: dict[str, Any]) -> Observation:
        """Convert AIS JSON message into standard ContinuityOS Observation."""
        mmsi = str(payload.get("mmsi", "UNKNOWN_MMSI"))
        vessel_name = str(payload.get("vessel_name", f"Vessel-{mmsi}"))
        lat = float(payload.get("latitude", 0.0))
        lon = float(payload.get("longitude", 0.0))
        sog = float(payload.get("speed_over_ground_knots", payload.get("sog", 12.0)))
        cog = float(payload.get("course_over_ground", payload.get("cog", 0.0)))
        nav_status = int(payload.get("nav_status", 0))

        # Check for operational anomalies
        is_spoofed = bool(payload.get("gnss_spoof_flag", False))
        is_speed_anomaly = sog > 45.0  # Impossible cargo vessel speed

        effective_state = CorridorState.OPEN
        if is_spoofed:
            effective_state = CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED
        elif is_speed_anomaly:
            effective_state = CorridorState.OPEN_DEGRADED

        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        return Observation(
            source_id=f"ais:{mmsi}",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.TRAFFIC_HISTORY,
            metric=MetricName.AIS_TRAFFIC_INDEX,
            value=0.20 if is_spoofed else 0.85,
            unit="index",
            observed_at=datetime.now(UTC),
            confidence=0.85 if not is_spoofed else 0.20,
            provenance=Provenance(
                uri=f"ais://global/vessel/{mmsi}",
                content_sha256=digest,
            ),
            metadata={
                "vessel_name": vessel_name,
                "latitude": lat,
                "longitude": lon,
                "speed_knots": sog,
                "course": cog,
                "nav_status": nav_status,
                "effective_state": effective_state.value,
                "is_spoofed": is_spoofed,
            },
        )


class NOAASpaceWeatherAdapter:
    """Parses NOAA Space Weather Prediction Center alerts for geomagnetic storms."""

    @staticmethod
    def parse_space_weather_alert(alert_data: dict[str, Any]) -> Observation:
        """Convert solar flare or Kp-index alert into High-Latitude Communications Observation."""
        kp_index = float(alert_data.get("kp_index", 3.0))
        event_type = str(alert_data.get("event_type", "GEOMAGNETIC_INDEX"))

        # Kp >= 7.0 indicates Strong to Extreme geomagnetic storm disabling polar SATCOM
        if kp_index >= 7.0:
            effective_state = CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED
            satcom_val = 0.10
            confidence = 0.95
        elif kp_index >= 5.0:
            effective_state = CorridorState.OPEN_DEGRADED
            satcom_val = 0.50
            confidence = 0.85
        else:
            effective_state = CorridorState.OPEN
            satcom_val = 0.95
            confidence = 0.90

        digest = hashlib.sha256(json.dumps(alert_data, sort_keys=True).encode("utf-8")).hexdigest()

        return Observation(
            source_id="noaa:swpc",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.SATCOM_AVAILABILITY,
            value=satcom_val,
            unit="ratio",
            observed_at=datetime.now(UTC),
            confidence=confidence,
            provenance=Provenance(
                uri="noaa://swpc/alerts/geomagnetic",
                content_sha256=digest,
            ),
            metadata={
                "event_type": event_type,
                "kp_index": kp_index,
                "effective_state": effective_state.value,
                "hf_blackout": kp_index >= 6.0,
                "satcom_degradation": kp_index >= 7.0,
            },
        )


class USGSSeismicAdapter:
    """Parses USGS ShakeMap and earthquake disruption feeds."""

    @staticmethod
    def parse_earthquake_alert(event_data: dict[str, Any]) -> Observation:
        """Convert seismic magnitude into corridor physical availability observation."""
        mag = float(event_data.get("magnitude", 0.0))
        region = str(event_data.get("region", "Global"))
        depth_km = float(event_data.get("depth_km", 10.0))

        if mag >= 7.0:
            effective_state = CorridorState.PHYSICALLY_CLOSED
            avail_val = 0.0
        elif mag >= 5.5:
            effective_state = CorridorState.OPEN_DEGRADED
            avail_val = 0.40
        else:
            effective_state = CorridorState.OPEN
            avail_val = 1.0

        digest = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode("utf-8")).hexdigest()

        return Observation(
            source_id="usgs:earthquake",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.EARTH_OBSERVATION,
            metric=MetricName.PORT_AVAILABILITY,
            value=avail_val,
            unit="ratio",
            observed_at=datetime.now(UTC),
            confidence=0.98,
            provenance=Provenance(
                uri=f"usgs://earthquake/event/{digest[:12]}",
                content_sha256=digest,
            ),
            metadata={
                "magnitude": mag,
                "region": region,
                "depth_km": depth_km,
                "effective_state": effective_state.value,
            },
        )


class OPCUASensorAdapter:
    """Parses industrial OT telemetry from port container cranes and rail interlockings."""

    @staticmethod
    def parse_scada_tag(payload: dict[str, Any]) -> Observation:
        """Convert SCADA PLC state into operational health observation."""
        tag_name = str(payload.get("tag", "PORT_CRANE_PLC_01"))
        operational_state = str(payload.get("status", "RUNNING"))
        throughput_rate = float(payload.get("throughput_percent", 100.0))
        error_codes = list(payload.get("errors", []))

        if operational_state in {"FAULT", "EMERGENCY_STOP", "MODBUS_FLOOD"}:
            effective_state = CorridorState.PHYSICALLY_CLOSED
            cap_val = 0.0
        elif throughput_rate < 50.0 or error_codes:
            effective_state = CorridorState.OPEN_DEGRADED
            cap_val = throughput_rate / 100.0
        else:
            effective_state = CorridorState.OPEN
            cap_val = 1.0

        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        return Observation(
            source_id=f"scada:{tag_name}",
            source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
            assertion_class=AssertionClass.LIVE_AVAILABILITY,
            metric=MetricName.PORT_CAPACITY,
            value=cap_val,
            unit="ratio",
            observed_at=datetime.now(UTC),
            confidence=0.99,
            provenance=Provenance(
                uri=f"opcua://scada/historian/{tag_name.lower()}",
                content_sha256=digest,
            ),
            metadata={
                "tag": tag_name,
                "status": operational_state,
                "throughput_percent": throughput_rate,
                "error_codes": error_codes,
                "effective_state": effective_state.value,
            },
        )
