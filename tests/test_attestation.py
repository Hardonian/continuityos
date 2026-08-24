"""Test suite for SCIF Hardware Attestation and Air-Gap Security Engine."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.attestation import SCIFAttestationEngine
from continuityos.service import create_app


class TestSCIFAttestationEngine:
    """Test TPM 2.0 PCR measurement and zero-egress network verification."""

    def test_nominal_scif_attestation(self) -> None:
        engine = SCIFAttestationEngine()
        cert = engine.perform_attestation(
            facility_id="SCIF-CARLING-01",
            facility_name="DND Carling Campus Main SCIF",
            outbound_network_interfaces_detected=0,
            secure_boot_enabled=True,
            memory_zeroization_verified=True,
        )

        assert cert.is_scif_certified is True
        assert cert.overall_compliance_score == 1.0
        assert len(cert.control_checks) == 5
        assert len(cert.certificate_signature_hex) > 64

    def test_failed_attestation_on_network_leak(self) -> None:
        engine = SCIFAttestationEngine()
        cert = engine.perform_attestation(
            facility_id="SCIF-LEAKING",
            facility_name="Compromised Facility",
            outbound_network_interfaces_detected=2,
            secure_boot_enabled=True,
            memory_zeroization_verified=True,
        )

        assert cert.is_scif_certified is False
        assert cert.overall_compliance_score < 1.0


class TestAttestationAPI:
    """Test attestation REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_attestation_verify_endpoint(self, client: TestClient) -> None:
        payload = {
            "facility_id": "SCIF-TEST",
            "facility_name": "Test Facility",
            "outbound_network_interfaces": 0,
        }
        resp = client.post("/v1/attestation/verify", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_scif_certified"] is True
