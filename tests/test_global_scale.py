"""Comprehensive test suite for ContinuityOS Global Scale & Enterprise Adoption modules."""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import ed25519

from continuityos.allied_defense import (
    CursorOnTargetExporter,
    DoDComplianceAuditor,
    Link16Adapter,
)
from continuityos.connectors import (
    AISStreamAdapter,
    EDIParser,
    GraphSynthesizer,
    NOAASpaceWeatherAdapter,
    OPCUASensorAdapter,
    USGSSeismicAdapter,
)
from continuityos.domain import CorridorState
from continuityos.ecosystem import (
    KubernetesController,
    KubernetesCRDGenerator,
    OPAGatekeeper,
    TerraformProviderSchema,
)
from continuityos.enterprise_db import (
    PostgreSQLStorageBackend,
    SQLiteStorageBackend,
    StoredRecord,
)
from continuityos.federation import SCIFEnclaveFederator
from continuityos.hsm import HSMInterface
from continuityos.hub import CorridorHubClient
from continuityos.insurance import InsuranceUnderwritingEngine
from continuityos.rating import ResilienceRatingEngine
from continuityos.sovereign import ClassificationLevel
from continuityos.sso import ABACPolicyEvaluator, PVICACValidator

SAMPLE_EDI_204 = """
ISA*00*          *00*          *ZZ*SHIPPER        *ZZ*CARRIER        *260911*1200*U*00401*000000001*0*P*>~
GS*SM*SHIPPER*CARRIER*20260911*1200*1*X*004010~
ST*204*0001~
B2**CNRU**PP~
B2A*00*SHP-2026-9901~
L11*BOL-990123*BM~
N1*SH*James Bay Lithium Mine*92*JBL01~
N1*CN*Sudbury Smelter Facility*92*SSF02~
S5*1*LD~
S5*2*UL~
OID*1*20000*LB*25000~
SE*10*0001~
GE*1*1~
IEA*1*000000001~
"""

SAMPLE_EDI_315 = """
ISA*00*          *00*          *ZZ*CARRIER        *ZZ*CONSIGNEE      *260911*1400*U*00401*000000002*0*P*>~
GS*QO*CARRIER*CONSIGNEE*20260911*1400*2*X*004010~
ST*315*0001~
B4*N*CONT-482019*VD*20260911*1400*MAEU~
N9*BM*BOL-OCN-7711~
R4*L*UN*YOK*Yokohama Container Terminal~
R4*D*UN*VAN*Port of Vancouver Centerm~
SE*6*0001~
GE*1*2~
IEA*1*000000002~
"""


def test_edi_204_parsing_and_synthesis() -> None:
    """Verify parsing of EDI 204 freight tenders and automated supply network synthesis."""
    shipment = EDIParser.parse_edi_204(SAMPLE_EDI_204)
    assert shipment.carrier_scac == "CNRU"
    assert shipment.shipper_name == "James Bay Lithium Mine"
    assert shipment.consignee_name == "Sudbury Smelter Facility"
    assert len(shipment.stops) == 2

    # Synthesize dependency graph and supply network
    graph = GraphSynthesizer.synthesize_dependency_graph([shipment])
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    net = GraphSynthesizer.synthesize_supply_network([shipment])
    assert "CNRU" in net.required_providers
    assert net.declared_redundancy >= 1


def test_edi_315_ocean_status() -> None:
    """Verify parsing of maritime ocean container status."""
    shipment = EDIParser.parse_edi_315(SAMPLE_EDI_315)
    assert shipment.carrier_scac == "MAEU"
    assert shipment.status == "VD"
    assert len(shipment.stops) == 2


def test_sap_bill_of_lading_parsing() -> None:
    """Verify parsing of SAP S/4HANA OData shipment JSON."""
    payload = {
        "DeliveryDocument": "DELIV-800192",
        "BillOfLading": "BOL-SAP-9988",
        "ForwardingAgent": "CP-KCS-RAIL",
        "ShipperPartyName": "James Bay Mine",
        "ShipToPartyName": "Hamilton Steel Mill",
        "TotalGrossWeightTonnes": 340.5,
        "CommodityDescription": "Cobalt High Purity",
    }
    shipment = EDIParser.parse_sap_bill_of_lading(payload)
    assert shipment.shipment_id == "DELIV-800192"
    assert shipment.carrier_scac == "CP-KCS-RAIL"
    assert shipment.weight_tonnes == 340.5


def test_telemetry_adapters() -> None:
    """Verify AIS, Space Weather, Seismic, and SCADA adapters."""
    # 1. AIS
    ais_obs = AISStreamAdapter.parse_ais_json(
        {
            "mmsi": "316001234",
            "vessel_name": "Arctic Navigator",
            "latitude": 72.5,
            "longitude": -85.0,
            "sog": 14.2,
            "cog": 270.0,
            "gnss_spoof_flag": False,
        }
    )
    assert ais_obs.source_id == "ais:316001234"
    assert ais_obs.confidence == 0.85

    # 2. Space Weather
    sw_obs = NOAASpaceWeatherAdapter.parse_space_weather_alert({"kp_index": 7.5})
    assert (
        sw_obs.metadata["effective_state"] == CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED.value
    )
    assert sw_obs.metadata["satcom_degradation"] is True

    # 3. Seismic
    eq_obs = USGSSeismicAdapter.parse_earthquake_alert({"magnitude": 7.4, "region": "Alaska"})
    assert eq_obs.metadata["effective_state"] == CorridorState.PHYSICALLY_CLOSED.value

    # 4. SCADA
    scada_obs = OPCUASensorAdapter.parse_scada_tag(
        {"tag": "VAN_CRANE_01", "status": "FAULT", "throughput_percent": 0.0}
    )
    assert scada_obs.metadata["effective_state"] == CorridorState.PHYSICALLY_CLOSED.value


def test_terraform_and_kubernetes_ecosystem() -> None:
    """Verify Terraform schema, K8s CRDs, controller reconciliation, and OPA gating."""
    tf_schema = TerraformProviderSchema.get_provider_schema()
    assert "provider" in tf_schema
    assert "continuity_corridor" in tf_schema["provider"]["resources"]

    crd = KubernetesCRDGenerator.generate_corridor_crd()
    assert crd["metadata"]["name"] == "missioncorridors.continuity.io"

    # Controller reconciliation
    res = KubernetesController.reconcile_corridor(
        spec={
            "metadata": {"name": "st-lawrence"},
            "spec": {"origin": "Montreal", "destination": "Atlantic"},
        },
        live_telemetry={"uninsurable": True},
    )
    assert res.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
    assert res.resilience_score == 0.35

    # OPA gatekeeper
    policy = {
        "name": "strict-defense-gate",
        "min_redundancy": 2,
        "max_closure_risk": 0.30,
        "min_assured_replenishment_days": 45.0,
    }
    eval_pass = OPAGatekeeper.evaluate_gate(
        policy,
        {"available_routes": 2, "closure_probability": 0.15, "assured_replenishment_days": 60.0},
    )
    assert eval_pass.allowed is True

    eval_fail = OPAGatekeeper.evaluate_gate(
        policy,
        {"available_routes": 1, "closure_probability": 0.55, "assured_replenishment_days": 10.0},
    )
    assert eval_fail.allowed is False
    assert len(eval_fail.violations) >= 3


def test_allied_defense_and_c2() -> None:
    """Verify US DoD IL5/IL6 DISA STIG auditor, Cursor on Target (CoT), and Link 16 tracks."""
    report = DoDComplianceAuditor.audit_system(target_level="IL6")
    assert report.is_accredited is True
    assert report.compliance_score == 1.0
    assert report.total_checks == 6

    # CoT XML
    xml_out = CursorOnTargetExporter.export_cot_xml(
        corridor_id="nsr-corridor",
        corridor_name="Northern Sea Route",
        lat=71.2,
        lon=-90.5,
        state=CorridorState.OPEN,
    )
    assert "<event" in xml_out
    assert "a-f-G-I-U-T" in xml_out

    # CoT GeoJSON
    json_out = CursorOnTargetExporter.export_cot_json(
        corridor_id="nsr-corridor",
        corridor_name="Northern Sea Route",
        lat=71.2,
        lon=-90.5,
        state=CorridorState.OPEN,
    )
    assert json_out["geometry"]["coordinates"] == [-90.5, 71.2]

    # Link 16 Track
    track = Link16Adapter.generate_track_report(
        corridor_id="panama",
        corridor_name="Panama Canal",
        lat=9.08,
        lon=-79.68,
        state=CorridorState.OPEN,
    )
    assert track.identity == "FRIEND"
    assert track.track_number == "T4021"


def test_hsm_cryptographic_interface() -> None:
    """Verify PKCS#11 HSM interface, TRNG entropy, signing, and signature verification."""
    hsm = HSMInterface()
    status = hsm.get_status()
    assert status.trng_entropy_rate_kb_s >= 1024.0
    assert status.health_verdict == "OPERATIONAL"

    data = b"Sovereign Defense Ledger Entry #4092"
    sig = hsm.sign_payload(data)
    assert hsm.verify_signature(sig, data) is True
    assert hsm.verify_signature(sig, b"TAMPERED DATA") is False


def test_enterprise_distributed_databases() -> None:
    """Verify SQLite WAL and PostgreSQL storage backend abstractions."""
    # SQLite
    sqlite_db = SQLiteStorageBackend(":memory:")
    rec = StoredRecord(
        record_id="REC-001",
        tenant_id="tenant-alpha",
        entity_type="corridor_snapshot",
        payload={"state": "OPEN", "burn_rate": 12.5},
    )
    sqlite_db.store_record(rec)
    fetched = sqlite_db.get_record("tenant-alpha", "REC-001")
    assert fetched is not None
    assert fetched.payload["state"] == "OPEN"

    # PostgreSQL
    pg_db = PostgreSQLStorageBackend()
    pg_db.store_record(rec)
    pg_fetched = pg_db.get_record("tenant-alpha", "REC-001")
    assert pg_fetched is not None
    assert pg_fetched.payload["burn_rate"] == 12.5


def test_hub_and_spoke_scif_federation() -> None:
    """Verify multi-enclave tactical reporting and one-way diode ingestion."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    corridors = [
        {"id": "c-01", "name": "Arctic Tactical Air Corridor", "state": "OPEN", "score": 0.95},
        {
            "id": "c-02",
            "name": "Deepwater Resupply Channel",
            "state": "OPEN_DEGRADED",
            "score": 0.65,
        },
    ]

    report = SCIFEnclaveFederator.create_tactical_report(
        enclave_id="SCIF-FORWARD-ALERT",
        classification="SECRET",
        corridors=corridors,
        signing_key=priv_key,
    )

    report_json = report.model_dump_json()

    # Ingest over diode
    valid, status, ingested = SCIFEnclaveFederator.ingest_diode_report(
        report_json, verifying_key=pub_key
    )
    assert valid is True
    assert status == "VERIFIED"
    assert ingested is not None
    assert len(ingested.corridor_summaries) == 2


def test_enterprise_sso_and_abac() -> None:
    """Verify DoD CAC / PIV X.509 certificate parsing and dynamic ABAC rules."""
    dn = "CN=SCOTT.HARDIAN.D.1928374650, OU=DND, OU=PKI, C=CA"
    identity = PVICACValidator.parse_x509_subject(dn)
    assert identity.identity_id == "1928374650"
    assert identity.citizenship == "CAN"
    assert identity.clearance_level == ClassificationLevel.PROTECTED_B

    # ABAC: Authorized
    auth, reason = ABACPolicyEvaluator.authorize_access(
        identity=identity,
        resource_classification=ClassificationLevel.PROTECTED_B,
        requires_canadian_eyes_only=True,
    )
    assert auth is True
    assert reason == "AUTHORIZED"

    # ABAC: Denied (clearance insufficient)
    auth_denied, reason_denied = ABACPolicyEvaluator.authorize_access(
        identity=identity,
        resource_classification=ClassificationLevel.SECRET,
    )
    assert auth_denied is False
    assert "insufficient" in reason_denied

    # ABAC: Denied (citizenship restricted)
    us_identity = PVICACValidator.parse_x509_subject("CN=JONES.BOB.9999, OU=DoD, C=US")
    auth_us, reason_us = ABACPolicyEvaluator.authorize_access(
        identity=us_identity,
        resource_classification=ClassificationLevel.PROTECTED_B,
        requires_canadian_eyes_only=True,
    )
    assert auth_us is False
    assert "restricted to Canadian Eyes Only" in reason_us


def test_global_corridor_hub() -> None:
    """Verify searching and pulling from Global Corridor Hub."""
    all_corridors = CorridorHubClient.list_corridors()
    assert len(all_corridors) >= 8

    malacca = CorridorHubClient.pull_corridor("malacca-strait")
    assert malacca is not None
    assert malacca.name == "Strait of Malacca"
    assert malacca.category == "MARITIME_CHOKEPOINT"
    assert malacca.annual_tonnage_millions == 1200.0


def test_war_risk_insurance_engine() -> None:
    """Verify war-risk premium calculations and underwriting certificate issuance."""
    res = InsuranceUnderwritingEngine.evaluate_marine_risk(
        corridor_name="Red Sea Bab-el-Mandeb",
        hull_value_usd=100_000_000.0,
        cargo_value_usd=50_000_000.0,
        has_verified_alternate_route=True,
    )
    assert res.premium_discount_percent == 28.5
    assert res.annual_premium_savings_usd > 0.0
    assert res.is_underwriting_approved is True

    cert = InsuranceUnderwritingEngine.issue_certificate(
        shipper="Maersk Line",
        corridor="Red Sea Bab-el-Mandeb",
        assessment=res,
    )
    assert cert.underwriting_grade == "PREFERRED_RISK"
    assert cert.discount_percentage == 28.5
    assert len(cert.sha256_digest) == 64


def test_resilience_rating_engine() -> None:
    """Verify standardized credit-style resilience rating agency scoring and certificate."""
    grade, scorecard = ResilienceRatingEngine.evaluate_entity(
        entity_name="Allied Arctic Strategic Supply Corridor",
        redundancy_count=3,
        assured_replenishment_days=75.0,
        recovery_lag_t5_days=5.0,
        has_shared_upstream_spof=False,
    )
    assert grade == "AAA"
    assert scorecard.composite_index >= 0.90

    cert = ResilienceRatingEngine.issue_rating_certificate(
        entity_name="Canadian Defence Minerals Corridor",
        redundancy_count=2,
        assured_replenishment_days=45.0,
        recovery_lag_t5_days=10.0,
    )
    assert cert.letter_grade in {"AAA", "AA", "A"}
    assert cert.rating_agency == "ContinuityOS Sovereign Rating Agency"
    assert len(cert.sha256_digest) == 64
