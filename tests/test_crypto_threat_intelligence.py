"""Comprehensive test suite for Bleeding-Edge Cryptography, Threat Detection, and AI Intelligence.

Tests:
  1. Post-Quantum Hybrid Signatures (Ed25519 + ML-DSA).
  2. Merkle Tree & Zero-Knowledge Verifiable Inclusion Proofs.
  3. Quantum-Resistant Sealed Intelligence Envelopes.
  4. GNSS EW Spoofing & Jamming Anomaly Detection.
  5. Port SCADA / OT Firmware & Command Burst Anomaly Detection.
  6. Maritime AIS Kinematic Violation & Teleportation Detection.
  7. Bayesian Supply Graph Cascade Forecaster.
  8. Self-Supervised Telemetry Stream Anomaly Detector.
  9. Explainable AI (XAI) Shapley Risk Attribution Explainer.
"""

from __future__ import annotations

import hashlib
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.crypto import (
    MerkleTree,
    SealedIntelligenceEnvelope,
    sha3_512_hash,
    shake256_digest,
    sign_hybrid_envelope,
)
from continuityos.domain import (
    CorridorAssessment,
    CorridorFactor,
    CorridorState,
    FactorAssessment,
)
from continuityos.graph import DependencyEdge, DependencyGraph, DependencyNode, NodeType
from continuityos.intelligence import (
    BayesianCascadeForecaster,
    TelemetryAnomalyForecaster,
    XAIRiskExplainer,
)
from continuityos.threat import (
    AISSpoofingDetector,
    GNSSAnomalyDetector,
    PortSCADAAnomalyDetector,
    ThreatDetectionEngine,
)


class TestBleedingEdgeCryptography:
    """Test post-quantum envelopes and Merkle inclusion proofs."""

    def test_sha3_and_shake256_hashing(self) -> None:
        h512 = sha3_512_hash("classified-evidence-payload")
        assert len(h512) == 128  # 512 bits in hex
        shake = shake256_digest("evidence", length=32)
        assert len(shake) == 64  # 32 bytes in hex

    def test_post_quantum_hybrid_signature_envelope(self) -> None:
        key = Ed25519PrivateKey.generate()
        payload = b"RESTRICTED DEFENSE TELEMETRY FEED"

        envelope = sign_hybrid_envelope(key, payload, key_id="key-us-dod-01")
        assert envelope.algorithm == "Ed25519+ML-DSA-65"
        assert envelope.verify_envelope(key.public_key(), payload) is True

        # Tamper payload -> verification fails
        assert envelope.verify_envelope(key.public_key(), b"TAMPERED PAYLOAD") is False

    def test_merkle_tree_inclusion_proofs_and_tamper_detection(self) -> None:
        leaf_data = [f"evidence_record_{i}".encode() for i in range(8)]

        leaf_hashes = [hashlib.sha256(d).hexdigest() for d in leaf_data]
        tree = MerkleTree(leaf_hashes)

        # Generate and verify proof for leaf #3
        proof = tree.generate_inclusion_proof(3)
        assert proof.record_index == 3
        assert proof.leaf_hash == leaf_hashes[3]
        assert proof.verify() is True

        # Mutate proof leaf hash -> verification fails
        proof.leaf_hash = hashlib.sha256(b"corrupted_leaf").hexdigest()
        assert proof.verify() is False

    def test_sealed_intelligence_envelope(self) -> None:
        recipient_key = hashlib.sha256(b"recipient_public_material").hexdigest()
        payload = {
            "intel_source": "COMSAT-4",
            "threat_level": "CRITICAL",
            "chokepoint": "kara-sea",
        }

        envelope = SealedIntelligenceEnvelope.seal(
            payload, recipient_key, classification="TOP_SECRET"
        )
        assert envelope.classification_level == "TOP_SECRET"
        assert envelope.encapsulation_scheme == "NIST-ML-KEM-768"
        assert len(envelope.ciphertext_payload_hex) > 0

        # Unseal and verify exact payload match
        unsealed = envelope.unseal(recipient_key)
        assert unsealed["intel_source"] == "COMSAT-4"
        assert unsealed["threat_level"] == "CRITICAL"


class TestCyberPhysicalThreatDetection:
    """Test cyber-physical detectors (GNSS, Port SCADA, AIS)."""

    def test_gnss_spoofing_detection(self) -> None:
        detector = GNSSAnomalyDetector()

        # Synthetic EW spoofing telemetry: high pseudorange variance and abnormal clock drift
        report = detector.analyze(
            pseudorange_residuals_m=[12.5, 45.2, -38.1, 29.4, 52.0],
            carrier_to_noise_ratios_db=[22.0, 24.5, 21.8],  # 20 dB drop
            clock_drift_ppm=14.2,  # Jump
            geometric_dop=7.5,
        )
        assert report.is_spoofed is True
        assert report.is_jammed is True
        assert report.threat.level == "CRITICAL"
        assert len(report.threat.indicators) >= 2
        assert "Inertial Navigation" in report.threat.remediation_recommendation

    def test_port_scada_ransomware_detection(self) -> None:
        detector = PortSCADAAnomalyDetector()

        report = detector.analyze(
            commands_per_second=240.0,  # Flood
            unauthorized_function_codes=[0x90, 0xFF],
            untrusted_ip_connections=4,
            plc_firmware_hashes={"crane_plc_01": "bad_hash_9999"},
            expected_firmware_hash="clean_firmware_1234",
        )
        assert report.ransomware_signature_detected is True
        assert report.unauthorized_plc_reprogramming is True
        assert report.threat.level == "CRITICAL"

    def test_ais_kinematic_teleportation_detection(self) -> None:
        detector = AISSpoofingDetector()

        # Vessel moving 120 km in 60 seconds = 7,200 km/h (impossible for cargo ship)
        report = detector.analyze(
            previous_lat=70.0,
            previous_lon=35.0,
            current_lat=71.0,
            current_lon=36.0,
            elapsed_seconds=60.0,
            reported_sog_knots=12.0,
        )
        assert report.is_kinematically_impossible is True
        assert report.mmsi_clone_detected is True
        assert report.threat.level == "CRITICAL"

    def test_unified_threat_engine_scan(self) -> None:
        engine = ThreatDetectionEngine()
        scan = engine.run_full_scan(
            "corridor/sector-arctic-chokepoint",
            gnss_residuals=[15.0, 25.0, 30.0],
            clock_drift_ppm=8.0,
        )
        assert scan.target_resource_ref == "corridor/sector-arctic-chokepoint"
        assert scan.gnss_threat.is_spoofed is True
        assert "GNSS EW Spoofing active" in scan.executive_summary


class TestAIAndMLIntelligenceLayer:
    """Test Bayesian cascade forecaster, stream anomaly detector, and XAI explainer."""

    def test_bayesian_cascade_forecaster(self) -> None:
        nodes = [
            DependencyNode(
                node_id="pnt_constellation", name="PNT", node_type=NodeType.SATCOM, criticality=0.9
            ),
            DependencyNode(
                node_id="escort_icebreaker",
                name="Escort",
                node_type=NodeType.SUPPLIER,
                criticality=0.85,
            ),
            DependencyNode(
                node_id="transit_lane",
                name="Transit Lane",
                node_type=NodeType.CORRIDOR,
                criticality=0.95,
            ),
            DependencyNode(
                node_id="destination_port", name="Port", node_type=NodeType.PORT, criticality=0.95
            ),
        ]
        edges = [
            DependencyEdge(
                source="pnt_constellation", target="transit_lane", dependency_strength=0.90
            ),
            DependencyEdge(
                source="escort_icebreaker", target="transit_lane", dependency_strength=0.80
            ),
            DependencyEdge(
                source="transit_lane", target="destination_port", dependency_strength=0.95
            ),
        ]
        graph = DependencyGraph(graph_id="polar-network", nodes=nodes, edges=edges)

        forecaster = BayesianCascadeForecaster()
        # Degrade PNT by 85%
        res = forecaster.forecast(
            graph,
            target_node="destination_port",
            observed_degradations={"pnt_constellation": 0.85},
        )

        assert res.target_node_id == "destination_port"
        assert res.failure_probability > 0.50
        assert "transit_lane" in res.node_probabilities
        assert "pnt_constellation" in res.high_risk_upstream_nodes

    def test_telemetry_stream_anomaly_forecaster(self) -> None:
        forecaster = TelemetryAnomalyForecaster()
        history = [12.0, 12.2, 11.8, 12.1, 12.0, 11.9, 12.3]  # Mean ~= 12.0, Std ~= 0.16

        # Normal value
        nom_score = forecaster.analyze_stream("water_level_m", history, current_value=12.1)
        assert nom_score.is_anomalous is False

        # Anomalous spike to 18.0 (>> 2.5 sigma)
        spike_score = forecaster.analyze_stream("water_level_m", history, current_value=18.0)
        assert spike_score.is_anomalous is True
        assert spike_score.z_score > 10.0
        assert spike_score.anomaly_confidence > 0.90

    def test_xai_shapley_risk_attribution_explainer(self) -> None:
        assessment = CorridorAssessment(
            assessment_id=uuid4(),
            corridor_id="vilkitsky-strait",
            overall_risk=0.78,
            confidence=0.92,
            state=CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED,
            factors=[
                FactorAssessment(
                    factor=CorridorFactor.CYBER,
                    risk=0.85,
                    confidence=0.95,
                    evidence_ids=[],
                    rationale="Heavy spoofing on L1/L2 GPS frequencies",
                ),
                FactorAssessment(
                    factor=CorridorFactor.ICE,
                    risk=0.45,
                    confidence=0.90,
                    evidence_ids=[],
                    rationale="Thin first-year ice",
                ),
                FactorAssessment(
                    factor=CorridorFactor.COMMERCIAL,
                    risk=0.20,
                    confidence=0.85,
                    evidence_ids=[],
                    rationale="Standard insurance active",
                ),
            ],
            missing_required_metrics=[],
            caveats=["PNT degraded"],
        )

        explainer = XAIRiskExplainer()
        xai = explainer.explain(assessment)

        assert xai.corridor_id == "vilkitsky-strait"
        assert xai.top_risk_driver == CorridorFactor.CYBER
        assert len(xai.factor_attributions) == 3
        # Cyber risk mass is 0.85 / 1.50 = 56.7%
        cyber_attr = next(a for a in xai.factor_attributions if a.factor == CorridorFactor.CYBER)
        assert cyber_attr.shapley_percentage > 50.0
        assert "CYBER" in xai.strategic_xai_summary
